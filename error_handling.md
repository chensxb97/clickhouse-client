# Error Handling in Query Function

## Scenario
Clickhouse Server runs with a custom middleware and returns custom error message with 503 response.

## Expectation
`client.query` function should return the custom error message from the Clickhouse Server.

## Reality
Returns `OperationalError` or a `DatabaseError` from the stack trace **without** the custom error message.
```
clickhouse_connect.driver.exceptions.OperationalError: HTTPDriver for http://localhost:8123 returned response code XXX
 25.8.2.29      UTC
```

## Investigation 
### query (Entry Point)
The query function performs either the `command` or `_query_with_context` function based on the query type.

- clickhouse_connect/driver/client.py (Line 190)
```
query_context = self.create_query_context(**kwargs)
if query_context.is_command:
    response = self.command(query,
                            parameters=query_context.parameters,
                            settings=query_context.settings,
                            external_data=query_context.external_data)
    if isinstance(response, QuerySummary):
        return response.as_query_result()
    return QueryResult([response] if isinstance(response, list) else [[response]])
return self._query_with_context(query_context)
```

### __query_with_context
The `_raw_request` function is where the client sends the request to the clickhouse server.
- clickhouse_connect/driver/httpclient.py (Line 227)
```
response = self._raw_request(body,
                                params,
                                headers,
                                stream=True,
                                retries=self.query_retries,
                                fields=fields,
                                server_wait=not context.streaming)
byte_source = RespBuffCls(ResponseSource(response))  # pylint: disable=not-callable
context.set_response_tz(self._check_tz_change(response.headers.get('X-ClickHouse-Timezone')))
query_result = self._transform.parse_response(byte_source, context)
query_result.summary = self._summary(response)
return query_result
```

### _raw_request
In this step, we notice that error handling is performed in `_error_handler` for non-200 response codes.

- clickhouse_connect/driver/httpclient.py (Line 384)
```
 if response.status in (429, 503, 504):
    if attempts > retries:
        self._error_handler(response, True)
    logger.debug('Retrying requests with status code %d', response.status)
elif error_handler:
    error_handler(response)
else:
    self._error_handler(response)
```
### _error_handler
- clickhouse_connect/driver/httpclient.py (Line 366)

It is observed that for any 500 http errors, the `err_str` variable is returned.
The `err_content` variable is also included if defined. The `get_response_data` function returns this variable.

```
if self.show_clickhouse_errors:
    try:
        err_content = get_response_data(response)
    except Exception:  # pylint: disable=broad-except
        err_content = None
    finally:
        response.close()

    err_str = f'HTTPDriver for {self.url} returned response code {response.status})'
    if err_content:
        err_msg = common.format_error(err_content.decode(errors='backslashreplace'))
        err_str = f'{err_str}\n {err_msg}'
else:
    err_str = 'The ClickHouse server returned an error.'

raise OperationalError(err_str) if retried else DatabaseError(err_str) from None
```

### _error_handler
The response body is expected to be returned in one of the following formats.

1. ZSTD compressed: If the content-encoding header is 'zstd', the body should be Zstandard-compressed bytes.
2. LZ4 compressed: If the content-encoding header is 'lz4', the body should be LZ4-compressed bytes.
3. Uncompressed: If there is no recognized compression, the body should be plain bytes.

To ensure that we return the error response properly, the request handler of the custom middleware should specify the 
correct encoding format in its `content-encoding` header.

```
def get_response_data(response: HTTPResponse) -> bytes:
    encoding = response.headers.get('content-encoding', None)
    if encoding == 'zstd':
        try:
            zstd_decom = zstandard.ZstdDecompressor()
            return zstd_decom.stream_reader(response.data).read()
        except zstandard.ZstdError:
            pass
    if encoding == 'lz4':
        lz4_decom = lz4.frame.LZ4FrameDecompressor()
        return lz4_decom.decompress(response.data, len(response.data))
    return response.data
```


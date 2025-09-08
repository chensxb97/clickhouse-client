# Error Handling in Query Function

## Scenario
Clickhouse Server runs with a custom middleware and returns custom error message with 503 response.

### Expectation
`client.query` function should return the custom error message from the Clickhouse Server.

### Reality
- main.py (Line 26)

```python
result = client.query('SELECT * FROM test_table')
```

Returned `OperationalError` or a `DatabaseError` from the stack trace **without** the custom error message.

```
# Stack Trace
clickhouse_connect.driver.exceptions.OperationalError: HTTPDriver for http://localhost:8123 returned response code 5XX
 25.8.2.29      UTC
```

### Problem
Error message returned from the custom middleware, did not start with an appropriate error code (prefix: "Code "). Due to the missing error code, the custom error message was not appended with the top-level error title.
```
if err_msg.startswith('Code'):
    err_str = f'{err_str}\n {err_msg}'
```
`err_str` was returned without `err_msg`.

### Solution
Every custom middleware error must be appended with an appropriate error code in this format `Code: XXX, (... remaining 
error msg).`
## Investigation
A deep dive from the entry point to the error handling function.

### query (Entry Point)
The query function performs either the `command` or `_query_with_context` function based on the query type.

- `clickhouse_connect/driver/client.py` (Line 177)

```python
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

### _query_with_context / command
- `_query_with_context`: `clickhouse_connect/driver/httpclient.py` (Line 190)
- `command`: `clickhouse_connect/driver/httpclient.py` (Line 313)

Both functions call the `_raw_request` function to enable the client to send the query request to the ClickHouse server.

```python
# command
method = 'POST' if payload or fields else 'GET'
response = self._raw_request(payload, params, headers, method, fields=fields)
if response.data:
    try:
        result = response.data.decode()[:-1].split('\t')
        if len(result) == 1:
            try:
                return int(result[0])
            except ValueError:
                return result[0]
        return result
    except UnicodeDecodeError:
        return str(response.data)
return QuerySummary(self._summary(response))
```

```python
# _query_with_context
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
- `clickhouse_connect/driver/httpclient.py` (Line 381)

In this step, we notice that error handling is performed in `_error_handler` for non-200 response codes.

```python
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
- `clickhouse_connect/driver/httpclient.py` (Line 363)

It is observed that for any 500 http errors, the `err_str` variable is returned.
The `err_content` variable is also included if defined. The `get_response_data` function returns this variable.
From here, we concluded that there is no issue with this function as it was able to return the variable in bytes properly.

Two variables are created: `err_msg` and `err_str`.

`err_msg` undergoes decoding and formatting before it gets appended to `err_str`. This variable was decoded without issues.

From the logs, we found that the logic that checks for the existence of the prefix `Code` did not execute, hence the `err_str` was not appended with the `err_msg` variable. 

Therefore, no custom error message was returned.

```python
if self.show_clickhouse_errors:
    try:
        err_content = get_response_data(response)
    except Exception:  # pylint: disable=broad-except
        err_content = None
    finally:
        response.close()

    err_str = f'HTTPDriver for {self.url} returned response code {response.status}'
    err_code = response.headers.get(ex_header)
    if err_code:
        err_str = f'HTTPDriver for {self.url} received ClickHouse error code {err_code}'
    if err_content:
        err_msg = common.format_error(err_content.decode(errors='backslashreplace'))
        if err_msg.startswith('Code'):
            err_str = f'{err_str}\n {err_msg}'
else:
    err_str = 'The ClickHouse server returned an error.'
```
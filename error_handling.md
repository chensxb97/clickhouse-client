# Clickhouse-connect Error Handling

## Scenario
- Clickhouse Server runs with a custom middleware and returns custom error message with 503 response.
- Expectation: Query function returns the custom error message.
- Reality: Returns OperationalError or DatabaseError objects

### query (Entry Point)
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
### _query_with_context
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
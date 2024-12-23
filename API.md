# API-Documentation
This is the documentation of the api-backend for the web-app and the script described in [README.md](./README.md)

## Structure
Since this is a json-backend api, everything is returned in the `json`-format.

```
{
    success: <true or false>,
    reason: <reason>,          // Only on success = false,
    data: {                    // The actual data
        ...
    }
}
```
- **`success`**: `true` when there are no errors, else `false`.
- **`reason`**: Only present if success is `false`. Refer to the ["Error-reasons"](#error-resons) below.
- **`data`**: The actual data. Refer to [each route below](#routes) in order to lookup what it returns. Will not be part of the response if there was an error.

#### Date-Format
This is the same for all dates:  
`YYYY-MM-DD HH:mm:ss`  
The time at the end will be always all `0`'s, since SQLite apparently always stores a time to a date.

## Routes
### Duration-API
```
/api/:year_start/:year_end/duration
```
This api-endpoint is used to determine the length of the school-year.  
**Parameters:**
- `year_start`: the year in which the school-year starts. Long form: e.g. 2024
- `year_end`: the year in which the school-year ends. Format as in `year_start`  

**Queries:**
- `?state`: Refer to ["Queries"](#query-parameters)

**Returns:**
```
{
    success: ...,
    reason:  ...,           
    data: {
        start: ...
        end: ...
    }
}
```
- **`start`:** The exact start of the school-year. `Null` if the first year is queried. See ["Filling the db"](./README.md#filling-the-db) for mor information.
- **`end`:** The exact end of the school-year.
Look at ["Date-format"](#date-format) for more information.
<br>

### Holiday-API
```
/api/:year_start/:year_end/holidays
```
This api-endpoint is used to retrieve the holidays for a specific state.
**Parameters:**
- `year_start`: the year in which the school-year starts. Short form: e.g. 24
- `year_end`: the year in which the school-year ends. Format as in `year_start`  

**Queries:**
- `?state`: Refer to ["Queries"](#query-parameters)

## Query-Parameters
- `?state`: One of the Austrian federal states

| State-values |
| ------ |
| `styria`        |
| `carinthia`     |
| `salzburg`      |
| `tirol`         |
| `burgenland`    |
| `upper_austria` |
| `lower_austria` |
| `vorarlberg`    |
| `vienna`    |

## Error-reasons
**Specialties:**  
Error-code: `404`  
The normal body is returned, but the `data`-field is empty, since there was no data that was found with what was provided.

**Errors due to invalid year:**
Error-code: `400`
- **`FORMAT`:** An invalid format was provided. Must be in short form: e.g. 24
- **`YEAR_SPAN_INVALID`:** The years must be following each other. That means that the `year_end` can't be a bigger than the year following the `year_start`.
    - `24` and `25`: Valid
    - `23` and `25`: Invalid
- **`INVALID_YEAR_ORDER`:** The `year_start` provided was bigger than the `year_end`.
- **`YEAR_START_TOO_SMALL`:** The `year_start` is smaller than the min. allowed year. Refer to ["Filling the db" in the README](./README.md#filling-the-db) for explanation.
- **`END_YEAR_TOO_BIG`:** The `year_end` was bigger than the following year of the current one.

<br>

**Error due to an invalid state/query:**
Error-code: `400`
- **`INVALID_QUERY`:** There was mor than on invalid query-parameters in the request.
- **`NO_STATE_PROVIDED`:** There was no state provided with `?state=...` in the query-parameters.
- **`INVALID_STATE`:** The state provided was not a valid one. Refer to [the valid states above](#query-parameters) for a list.

<br>

**Server-side errors:**
Error-code: `500`
- **`SERVER_ERROR`:** An unexpected error occurred on the server. Contact the one who runs it, since they can read the error in the logs.

## Errors on the server-side
Errors will be logged to `stdout`. The errors are handed up as they are thrown / provided by the db. But there is one exception:
- `DB_SUSPICIOUS`: The db provided data in a format that wasn't expected. Manual intervention is needed. This is the only error-report which will be filed with a severity of `WARNING`, since it make ths api still return `data` (an empty object / `{}`).
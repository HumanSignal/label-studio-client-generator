# label-studio-client-generator

## How to Contribute
1. Create a new or modify [YAML OpenAPI spec](https://swagger.io/docs/specification/about/) for Label Studio endpoints.
   For example, `./fern/openapi/resources/comments.yaml`:
   ```yaml
   paths:
    /api/comments:
      get: ...
  	  post: ...
   components:
    schemas:
      Comments: ...
    requestBodies:
      api_comments_create: ...
   ```
    - `paths` : contain API path
    - `components` (optional): components to reuse in `responses`
    - `requestBodies` (optional): request bodies specification to reuse in requests' `requestBody`
2. Run the sync script to automatically update `overrides.yaml` (for fern's [Overlay Customizations](https://buildwithfern.com/learn/api-definition/openapi/overlay-customizations)). You can use either method:
   ```bash
   python scripts/sync_overrides.py
   # or, from any python env
   uv run scripts/sync_overrides.py
   ```
   This will add the necessary references and SDK method configurations to `overrides.yaml`. The script will:
   - Add `$ref` references to your resource YAML files
   - Configure SDK method names using the file and operation names
   - Set the audience to "public"
   This will define the public methods called `client.comments.list()` and `client.comments.create()`. Read more about [Fern's OpenAPI extensions](https://buildwithfern.com/learn/api-definition/openapi/extensions)
3. Create a PR in `label-studio-client-generator` using [Follow-Merge workflow](https://www.notion.so/214a17976c254100a4c261ec800cf3e8?pvs=21). For example, push a branch called `fb-PRJ-123-update-comments-api` 
4. Ensure PR is created in `label-studio-sdk` and Label Studio repo
5. Update added endpoints in Django code.
6. Add integration tests with newly added functions in LS: `https://github.com/HumanSignal/label-studio/tree/develop/label_studio/tests/sdk`
   

### Create openapi.yaml

```
swagger2openapi --yaml --outfile ./fern/openapi/openapi.yaml http://localhost:8080/docs/api?format=openapi
```

### Generate docs

```
fern generate --docs
```

#### Generate docs locally
```
fern docs dev
```

## Add custom docs

Go to `fern/openapi/overrides.yaml` and modify fields keeping the structure as in `fern/openapi/openapi.yaml`. For example

```
paths:
  /api/projects/:
    post:
      summary: List of Projects
```
-->
```
paths:
  /api/projects/:
    post:
      summary: A new title to be replaced
    get:
      description: and another update in description `/get` endpoint.
```

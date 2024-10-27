# Refuel.ai LLM Application Server Take-Home
## by Shivanshu Gupta

Live at [llm-app.shivgupta.xyz](https://llm-app.shivgupta.xyz/).
Codebase accessible [here](https://bitbucket.org/shiv248/refuel-ai-coding-exercise/src/).

### LLM Application Server Project Summary

This project involved building an API server for managing LLM-based applications, enabling users to define, use, and monitor applications powered by _OpenAI_ LLM.
Key features include endpoints to create new applications with specific prompt and schema configurations, process requests via these applications,
and retrieve logs of processed traffic for analysis. The server will leverage one of OpenAI's LLM models (`gpt-4o-mini`) as the application processor.
It also has simple deployment method for docker build/run and scalable deployment using docker-compose. This project also includes tests such as integration and unit,
in addition it handles schema validation and data type validation. For the LLM side if data generation isn't suited there are retry mechanisms in place for LLM call
chaining and retrieving previous attempts with errors embedded within prompts. The project is built in _Python_ using _OpenAI_ for LLM, _LangChain_ for integration,
_LangGraph_ for LLM orchestration, _Pydantic_ for data validation,_MongoDB_ for data storage at scale, _FastAPI_ and _Uvicorn_ for asynchronous request handling.
I will go over how to run the application, deploy it and briefly explain parts of the project.

### Running the Application via Make

This project has a `Makefile` to ease interacting with it, do view it before you run any commands!

1. `make install` will:

   - Create a virtual environment
   - `pip install` all the requirements
   - Have a ready `venv` for you to manually activate in your shell if you'd like

2. Add your API key to `src/.env`, an example `.env` has been provided, before the next steps.

3. `make run` will:

   - Run `install` and make sure you have a venv
   - Start the FastAPI server on [localhost:8000](http://localhost:8000)

4. `make tests` will:

   - Run `install` and make sure you have a venv
   - Discover and run integration and unit tests for the project

5. `make clean` will:

   - Remove the virtual environment
   - Clean up any cache files or directories

### Running the Application via Docker

Follow these steps to get the application up and running:

1. Make sure you have Docker and Docker Compose installed on your system. If not, follow these instructions:

   - **Docker**:

     - For Windows and macOS, download and install Docker Desktop from [Docker's official website](https://www.docker.com/products/docker-desktop).
     - For Linux, follow the instructions on [Docker's official documentation](https://docs.docker.com/engine/install/).

   - **Docker Compose**:
     - Docker Desktop includes Docker Compose. For Linux, follow the instructions on [Docker Compose's official documentation](https://docs.docker.com/compose/install/).

2. Add your API key to `src/.env`, an example `.env` has been provided, before the next steps.
3. Build the project:
   - **Docker**:
     - Navigate to the root directory.
     - `docker build -t llm-app .`
     - This will build a standalone container of the llm application

   - **Docker Compose**:
     - Navigate to the `/deploy` folder
     - `docker-compose up --build`

4. Access the project:
   - Once the container(s) are up and running...
   - You can now interact with an LLM application
   - There are prefilled objects to play around with

   - **Docker**:
     - Using your favorite browser navigate to
     - [localhost:8000](http://localhost:8000)

   - **Docker Compose**:
     - Using your favorite browser navigate to
     - [localhost:80](http://localhost:80)

5. with Docker Compose:
   - You have access to an online mongodb GUI called `mongo-express`
   - Available on [localhost:1234](http://localhost:1234)
   - The basicAuth credentials are "`admin`:`pass`"

6. To stop the application
   - Press `Ctrl+C` in the terminal.
7. To clean-up:
   - **Docker**:
     ```
       docker container prune
       docker image prune -a
       docker volume prune
       docker network prune
       docker system prune -a --volumes
        ```
     - Note this cleans up _All_ unused resources

   - **Docker Compose**:
     ```
     docker-compose down -v --rmi all
     ```
     This will stop and remove the containers, networks, and volumes created by `docker-compose up`.

### Briefly About The Project
- Uses JSON or dict for data being passed around within the application
- Asynchronous server for low latency non-blocking responses
- Attempt at aggressive data validation and bespoken application schema validation using Pydantic V1
- Python tests for components unit and integrations, Frontend for testing, Postman collections for testing
- Dynamic database handling, in-mem(Docker build) or MongoDB(Docker-compose), and moduler for future data middleware
- Custom logging for easy import into any observability framework
- LangGraph retry mechanism with output data validation and output correction
- LangChain for flexable LLM provider switching
- Scalable with 3 replicas and a round-robin Nginx load balancer, data agnostic application with MongoDB as golden source

---

### Endpoints

#### 1. **GET /** - Serve Index Page
Returns the frontend HTML for the application�s main page.

- **Path**: `/`
- **Method**: `GET`
- **Response**:
  - **Success (200)**: Returns `index.html` from the `/static` directory.

#### 2. **POST /applications** - Create Application
Creates a new application with a unique identifier and defined configuration schema.

- **Path**: `/applications`
- **Method**: `POST`
- **Request Body**:
  - **Fields**:
    - `prompt_config` (string): Configuration for LLM application prompt.
    - `input_schema` (object): Schema describing the expected input structure.
    - `output_schema` (object): Schema describing the expected output structure.
  - **Example**:
    ```json
    {
      "prompt_config": "Analyze the sentiment of the text...",
      "input_schema": {
        "type": "object",
        "properties": {
          "review_text": {"type": "string"}
        },
        "required": ["review_text"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "sentiment": {"type": "string"}
        }
      }
    }
    ```

- **Response**:
  - **Success (200)**:
    - Returns a JSON object with `application_id`.
    - **Example**:
      ```json
      {
        "application_id": "123e4567-e89b-12d3-a456-426614174000"
      }
      ```
  - **Error (422)**: Returns validation errors.
    - **Example**:
      ```json
      {
        "detail": "Field 'prompt_config' is missing."
      }
      ```

#### 3. **DELETE /applications/{application_id}** - Delete Application
Deletes an existing application by its unique identifier.

- **Path**: `/applications/{application_id}`
- **Method**: `DELETE`
- **Parameters**:
  - `application_id` (string): The unique identifier of the application to delete.

- **Response**:
  - **Success (204)**: Indicates successful deletion.
  - **Error (404)**: Returns if the application does not exist.
    - **Example**:
      ```json
      {
        "detail": "Application not found"
      }
      ```

#### 4. **POST /applications/{application_id}/completions** - Generate LLM Completion
Generates a response based on the application�s configuration and user input, invoking the LLM.

- **Path**: `/applications/{application_id}/completions`
- **Method**: `POST`
- **Parameters**:
  - `application_id` (string): The unique identifier of the application for which to generate a response.
- **Request Body**:
  - JSON object matching the `input_schema` of the specified application.
  - **Example**:
    ```json
    {
      "review_text": "This product is amazing!"
    }
    ```

- **Response**:
  - **Success (200)**: JSON response generated by the LLM based on the provided input.
    - **Example**:
      ```json
      {
        "sentiment": "positive"
      }
      ```
  - **Error (422)**: Returns if input validation against `input_schema` fails.
    - **Example**:
      ```json
      {
        "detail": "Field 'review_text' is missing."
      }
      ```
  - **Error (404)**: Returns if the application does not exist.
    - **Example**:
      ```json
      {
        "detail": "Application not found"
      }
      ```

#### 5. **GET /applications/{application_id}/completions/logs** - Retrieve Application Logs
Fetches the log of interactions between user and app for a specified application.

- **Path**: `/applications/{application_id}/completions/logs`
- **Method**: `GET`
- **Parameters**:
  - `application_id` (string): The unique identifier of the application for which to retrieve logs.

- **Response**:
  - **Success (200)**: Array of logs documenting each interaction.
    - **Example**:
      ```json
      [
        {
          "sender": "user",
          "msg": "This product is amazing!",
          "timestamp": "2024-01-01T12:00:00Z"
        },
        {
          "sender": "ai",
          "msg": {"sentiment": "positive"},
          "timestamp": "2024-01-01T12:00:01Z"
        }
      ]
      ```
  - **Error (404)**: Returns if the application does not exist.
    - **Example**:
      ```json
      {
        "detail": "Application not found"
      }
      ```

### Future Improvements
- Better handle validation errors, more detail
- Rather than returning errors one at a time append them to a list and return them all together for validate_app_construct_input
- Be able to handle nested json in completion for validate input, validate_output_against_schema
- Dynamically create pydantic BaseModel using pydantic.create_model
- Better integration testing for mock external apis, mongodb, llm calls, ect.
- WebSocket completion endpoint for streaming tokens
- Prompt conversation/logging summary, token limitation
- More extensive input validation and cleaning
- Probably don't log during integration test
- Better logging handling for json parsing json data when saving to file
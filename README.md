# graph_to_agent

For Vision-Statement see: [Vision.md](READ_ME%2FVision.md)

# Motivation

1. **Understand the motivation**
    - [Vision.md](READ_ME%2FVision.md)
    - [V](https://cv-gieklps3ea-uc.a.run.app/graph_to_agent_normative_approach)
    - [linkedin_article](https://www.linkedin.com/pulse/proposal-re-use-re-design-flawed-reward-system-git-all-kilian-lehn-oj2ze%3FtrackingId=2dJYCDeFmOoTpzMEszsqmA%253D%253D/?trackingId=2dJYCDeFmOoTpzMEszsqmA%3D%3D)

## Git Workflow Rules

1. **Branching Strategy:**
    - Each developer should work on their own development branch (e.g. feature-... development branch).
    - The `main` branch should only be updated through pull requests.
    - Pull requests to the `main` branch require a review before being merged.
    - Delete feature branches once they are merged into `main`.

2. **Commit Messages:**
    - Write clear and concise commit messages describing the changes made.
    - Use the imperative mood, e.g., "Add feature" not "Added feature" or "Adds feature".

3. **Conflict Resolution:**
    - Resolve merge conflicts in your development branch before submitting a pull request.
    - Keep your branch updated with the latest changes from `main` to minimize conflicts.

4. **Code Review:**
    - Actively participate in code review processes.
    - Reviewers should ensure code quality, functionality, and adherence to design principles.

# Specs

1. **Status:** MVP
2. **Architecture:**
    1. **Involved Platforms:**
        1. GCP
            1. **Stack:**
                1. Cloud Run (europe-west3-docker.pkg.dev/...)
                2. BQ
4. **.env**

# ENV-Configs

NUM_STEPS=10 (todo :: UI :: DFS search of user input)

MODEL=gpt-3.5-turbo-16k-0613 (todo :: UI :: Dropdown of models)

## Credentials

BQ_CLIENT_SECRETS={*****}

OPENAI_API_KEY=****

## Endpoints

OPENAI_BASE_URL=https://api.openai.com/v1/chat/completions

## Tables

ADJACENCY_MATRIX_DATASET_ID=graph_to_agent_adjacency_matrices
MULTI_LAYERED_MATRIX_DATASET_ID=graph_to_agent_multi_layered_metrices
ANSWER_CURATED_CHAT_COMPLETIONS=graph_to_agent_answer_curated_chat_completions
CURATED_CHAT_COMPLETIONS=graph_to_agent_chat_completions
RAW_CHAT_COMPLETIONS=graph_to_agent_raw_chat_completions
GRAPH_DATASET_ID=graph_to_agent
EDGES_TABLE=edges_table
NODES_TABLE=nodes_table

## Local Dirs

TEMP_RAW_CHAT_COMPLETIONS_DIR=temp_raw_chat_completions
TEMP_MULTI_LAYERED_MATRIX_DIR=temp_multi_layered_matrix
TEMP_CHECKPOINTS_GPT_CALLS=temp_checkpoints_gpt_calls
LOG_DIR_LOCAL=./temp_log

# Video-Agenda

1. control + shift --> default :D
2. control c + v
3. explain multi select difference between custom function, agent and assistant
4. modi msg passing
5. how to read proposal
6. explain roadmap
7. explain interest in simulation
    1. law of physics connected with msg. passing weights/ the more msgs/ the more info one msg carries, the higher the
       gravity of a node
    2. conways game of life
    3. llama-index --> language corpus via edges
8. explain different dimensions if somebody uses a pre-trained/ fine tuned model 
9. Explain the sheer infinite statistical possibilities, starting with the two layers
   1. explain the difference between the two layers
   2. distance matrix
   3. social interaction simulation by msg. protocols
   4. Agent behaviour with dynamic environment





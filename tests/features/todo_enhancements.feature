Feature: Brownfield Todo App Enhancements (mm-learning-group-1)
  Background:
    Given the Todo App is running

  # ---------------------------------------------------------------------------
  # User Story 1: Persistent SQLite Storage
  # ---------------------------------------------------------------------------

  Scenario: Persisted tasks remain available after application restart
    Given the application is configured to use persistent SQLite storage
    When I create a task with title "<title>"
    And I record the created task ID
    And I restart the Todo App
    Then retrieving the task by the recorded task ID should succeed
    And the returned task should have title "<title>"

  Scenario: Persisted updates remain after application restart
    Given the application is configured to use persistent SQLite storage
    When I create a task with title "<title>"
    And I record the created task ID
    And I update the task status to "done"
    And I restart the Todo App
    Then retrieving the task by the recorded task ID should succeed
    And the returned task should have status "done"

  Scenario: Persisted deletion remains after application restart
    Given the application is configured to use persistent SQLite storage
    When I create a task with title "<title>"
    And I record the created task ID
    And I delete the task by the recorded task ID
    And I restart the Todo App
    Then retrieving the task by the recorded task ID should fail with "not found"

  Scenario: SQLite enforces non-empty title at the storage layer
    Given the application is configured to use persistent SQLite storage
    When a task is persisted with an empty title via the data layer
    Then the operation should fail
    And the error should indicate "title non-empty"

  # ---------------------------------------------------------------------------
  # User Story 2: Task Edit & Delete CRUD
  # ---------------------------------------------------------------------------

  Scenario: Edit an existing task title successfully
    Given a task exists with title "<original_title>"
    And I record the created task ID
    When I update the task title to "<updated_title>"
    Then retrieving the task by the recorded task ID should succeed
    And the returned task should have title "<updated_title>"

  Scenario: Edit trims whitespace from title and saves trimmed value
    Given a task exists with title "<original_title>"
    And I record the created task ID
    When I update the task title to "  <updated_title>  "
    Then retrieving the task by the recorded task ID should succeed
    And the returned task should have title "<updated_title>"

  Scenario: Edit rejects an empty task title
    Given a task exists with title "<original_title>"
    And I record the created task ID
    When I update the task title to ""
    Then the task update should fail
    And retrieving the task by the recorded task ID should have title "<original_title>"

  Scenario: Edit rejects a whitespace-only task title
    Given a task exists with title "<original_title>"
    And I record the created task ID
    When I update the task title to "   "
    Then the task update should fail
    And retrieving the task by the recorded task ID should have title "<original_title>"

  Scenario: Edit rejects invalid priority
    Given a task exists with title "<title>"
    And I record the created task ID
    When I update the task priority to "<invalid_priority>"
    Then the task update should fail
    And the error should indicate "invalid priority"

  Scenario: Update due date set and clear
    Given a task exists with title "<title>"
    And I record the created task ID
    When I set the due date to "<due_date_value>"
    Then retrieving the task by the recorded task ID should show due date "<due_date_value>"
    When I clear the due date
    Then retrieving the task by the recorded task ID should show no due date

  Scenario: Delete an existing task successfully
    Given a task exists with title "<title>"
    And I record the created task ID
    When I delete the task by the recorded task ID
    Then retrieving the task by the recorded task ID should fail with "not found"

  Scenario: Delete a non-existent task returns not found
    When I delete the task with task ID "<non_existent_task_id>"
    Then the task deletion should fail with "not found"

  Scenario: Edit a non-existent task returns not found
    When I update the task with task ID "<non_existent_task_id>" to status "done"
    Then the task update should fail with "not found"

  Scenario: Retrieve a non-existent task returns not found
    When I retrieve the task by task ID "<non_existent_task_id>"
    Then the task retrieval should fail with "not found"

  # ---------------------------------------------------------------------------
  # User Story 3: Multi-Condition Search & Status Filtering
  # ---------------------------------------------------------------------------

  Scenario Outline: Filter and search tasks by keyword and status
    Given tasks "Write report" (pending) and "Write tests" (done) exist
    When I search for tasks with query "<query>" and status "<status>"
    Then the corresponding filtered task list should be returned

    Examples:
      | query | status  |
      | Write | pending |
      | Write | done    |

  Scenario: Search returns matching tasks only for the given keyword and status
    Given tasks "Learn AI-driven SDLC" (pending) and "Buy coffee" (pending) exist
    When I search for tasks with query "Learn" and status "pending"
    Then the corresponding filtered task list should be returned

  Scenario: Filtering by status returns only tasks with that status
    Given tasks "Task A" (pending) and "Task B" (done) exist
    When I search for tasks with query "" and status "done"
    Then the corresponding filtered task list should be returned

  Scenario Outline: Search rejects invalid status value
    Given tasks "Write report" (pending) and "Write tests" (done) exist
    When I search for tasks with query "Write" and status "<invalid_status>"
    Then the search should fail
    And the error should indicate "invalid status"

    Examples:
      | invalid_status |
      | unknown        |
      | DONEE          |

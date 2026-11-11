# Todo App Requirements

## Purpose

As a user, I want my todos to be saved automatically and remain available when I reopen the app, so that I can reliably manage tasks over time.

## Scope and assumptions

- The MVP is a local, single-user todo app using SQLite for persistence.
- Users can create, edit, complete, delete, search, and filter todos.
- Search and filters affect only the displayed view; they never modify stored data.
- Duplicate todo titles are allowed.
- Search is case-insensitive and searches titles.
- Multi-user and cross-device synchronization are out of scope.

## Data model and persistence

Each todo stores at minimum:

- `id`: unique, stable, system-generated identifier.
- `title`: trimmed text, between 1 and 255 characters.
- `completed`: completion state.
- `created_at`: timestamp set automatically at creation.
- `updated_at`: timestamp set at creation and updated whenever the title or completion state changes.

All operations target todos by `id`, never by list position or index. Successfully saved todos are persisted in SQLite and remain available after app restart or reload with the same IDs, titles, and completion states. A missing database is initialized automatically if supported by the runtime.

Deletion is permanent in the MVP and requires confirmation. `updated_at` is not changed by deletion because the record is removed. Undo and soft deletion are future enhancements.

## Functional requirements and acceptance criteria

### Create and validation

- Given a user submits a valid title, when it is saved, then a todo is created in SQLite and appears in the list.
- A valid title is non-empty after trimming and no longer than 255 characters.
- Leading and trailing whitespace is trimmed before saving.
- Empty or whitespace-only titles are rejected with a clear validation message.
- Titles exceeding 255 characters are rejected with a clear validation message.
- A created todo receives a unique stable ID, and `created_at` and `updated_at` are set automatically.

### Edit

- Given a todo exists, when the user edits its title and saves valid changes, then the title is updated in the UI and SQLite.
- Editing retains the todo's ID and updates `updated_at`.
- The create-title validation rules also apply when editing.
- Canceling an edit discards unsaved changes.
- If validation or persistence fails, the last successfully saved todo remains intact and an error is shown.

### Completion state

- Given a todo exists, when the user toggles completion, then the change is persisted and `updated_at` is updated.
- The UI reflects the successfully persisted completion state.

### Delete

- Given a todo exists, when the user chooses Delete, then the app asks for confirmation before permanent deletion.
- When deletion is confirmed and succeeds, the todo is removed from the UI and SQLite.
- If deletion is canceled, the todo remains unchanged.
- If deletion fails, the todo remains visible and an error is shown.
- Deleting a todo does not alter another todo's ID or data.

### Search and filters

- Search matches todo titles case-insensitively and updates as the query changes.
- Status filter choices are `All`, `Active` (not completed), and `Completed`.
- When search and a status filter are both active, only todos satisfying both constraints are shown (AND behavior).
- If no todos match, the UI shows a clear “No results” state.
- Clearing the query or resetting a filter updates the displayed result set appropriately.
- Search and filtering do not write to or otherwise modify stored todos.
- If a search/filter operation fails, the UI shows an error or safely falls back to the full list; it must not misrepresent the failure as “No results.”

### Startup and persistence

- Given previously saved todos exist, when the app restarts or reloads, then the todos load from SQLite with their prior IDs, titles, and completion states.
- If loading fails, the app shows a clear data-unavailable error rather than presenting an empty list as a successful load.

## Non-functional requirements

- SQLite is the persistence layer; todos must not exist only in memory.
- Loading a few thousand records should complete in approximately 1–2 seconds on a typical developer machine.
- The app remains usable and does not crash when database reads or writes fail.
- Failed operations must not corrupt or silently discard existing stored todos.
- User-provided values in database queries must be handled with parameterized queries.
- Database transactions should be used where appropriate to make writes atomic.
- User-facing errors must be understandable and must not expose raw SQL or implementation details.

## Error handling and data consistency

- On startup read/database failure, show a clear data-unavailable error and do not imply that loading succeeded.
- On create, edit, toggle, or delete write failure, show an actionable error, keep the UI usable, and retain the last successfully persisted state.
- A failed operation must not be presented as successfully saved.
- After a successful operation, the UI reflects the persisted state.
- Validation errors appear near the relevant input and prevent the database write.
- Retry controls and offline action queuing are not MVP requirements.

## Edge cases and concurrency

- Handle blank, whitespace-only, and over-limit titles on both create and edit.
- Handle editing or toggling while search or filters are active; operations must still target the correct todo by ID.
- Handle deleting the only result in the current filtered/search result set without leaving a stale or broken list.
- Handle clearing search while a status filter remains active, and clearing a filter while search remains active.
- Rapid sequential updates to one todo (for example, toggle then edit) must not overwrite a newer successful update with stale state. The UI and database should reflect the latest successful action.
- Multiple tabs/windows and conflict resolution are outside MVP scope. Database locking or transient errors must still be handled gracefully without data corruption.

## Nice-to-have / future scope

- Undo for deletes or edits; soft deletion and later purge.
- Retry controls and offline write queues.
- Persisting search/filter state across app restarts.
- Sorting by creation date, modification date, or completion state.
- Drag-and-drop ordering and keyboard shortcuts.
- Multi-window conflict detection, multi-user access, and cross-device synchronization.
- Schema migration tooling and expanded diagnostic logging.

## Manual QA cases

1. Create a valid todo; verify it appears, has an ID and timestamps, and remains after restart.
2. Create titles with leading/trailing whitespace; verify saved whitespace is trimmed.
3. Submit an empty or whitespace-only title; verify save is blocked with an explanation.
4. Submit a title longer than 255 characters; verify save is blocked with an explanation.
5. Edit a todo; verify its ID remains the same, its title changes, and `updated_at` changes.
6. Cancel an edit; verify unsaved changes are discarded.
7. Attempt an invalid edit; verify the saved title remains intact.
8. Toggle completion; verify the state and `updated_at` persist after reload.
9. Start a deletion and cancel; verify the todo remains. Confirm deletion; verify only that todo is removed.
10. Simulate database read/write failures; verify a clear error, no crash, and no false success or data corruption.
11. Search with different capitalization; verify matching is case-insensitive and results update as the query changes.
12. Test All, Active, and Completed filters, then combine each with a search query; verify AND behavior.
13. Search for a non-matching title; verify the “No results” state. Clear search/filter independently and verify the expected results return.
14. Delete the only visible result under a filter/search; verify the list transitions to the correct empty state.
15. Toggle and immediately edit a todo; verify the latest successful state appears in both the UI and persisted data.
16. Delete one todo and then edit or toggle another; verify the operation targets the correct stable ID.
17. Load a few thousand todos; verify loading completes in approximately 1–2 seconds on a typical developer machine.

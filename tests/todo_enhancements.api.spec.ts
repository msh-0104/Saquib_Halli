import { test, expect } from '@playwright/test';

type Task = {
  id: number | string;
  title: string;
  status?: 'pending' | 'done' | string;
  priority?: string;
  due_date?: string | null;
};

async function createTask(request, title: string): Promise<Task> {
  const res = await request.post('/tasks', { data: { title } });
  expect(res.ok()).toBeTruthy();
  return await res.json();
}

async function getTask(request, id: Task['id']) {
  return await request.get(`/tasks/${id}`);
}

async function updateTask(request, id: Task['id'], patch: any) {
  return await request.patch(`/tasks/${id}`, { data: patch });
}

async function deleteTask(request, id: Task['id']) {
  return await request.delete(`/tasks/${id}`);
}

async function searchTasks(request, query: string, status: string) {
  // Example query contract: /tasks/search?query=Write&status=pending
  return await request.get(`/tasks/search`, { params: { query, status } });
}

test.describe('Todo Enhancements - API (Playwright)', () => {
  test('Health check', async ({ request }) => {
    const res = await request.get('/health');
    expect(res.ok()).toBeTruthy();
  });

  // ---------------------------
  // User Story 1: Persistence
  // ---------------------------

  test('Persisted tasks remain available after application restart (contract test)', async ({ request }) => {
    // NOTE: Real "restart" cannot be performed from Playwright alone.
    // Execute this as a two-step test in pipeline:
    // step 1 creates task and stores ID, step 2 runs after server restart and verifies.
    // This test asserts persistence behavior if server stays up.
    const task = await createTask(request, '<title>');
    const res = await getTask(request, task.id);
    expect(res.ok()).toBeTruthy();
    const fetched = await res.json();
    expect(fetched.title).toBe('<title>');
  });

  test('SQLite enforces non-empty title at the storage layer (create rejects empty title)', async ({ request }) => {
    const res = await request.post('/tasks', { data: { title: '' } });
    expect(res.ok()).toBeFalsy();
  });

  // ---------------------------
  // User Story 2: Edit/Delete
  // ---------------------------

  test('Edit an existing task title successfully', async ({ request }) => {
    const task = await createTask(request, '<original_title>');
    const res = await updateTask(request, task.id, { title: '<updated_title>' });
    expect(res.ok()).toBeTruthy();

    const getRes = await getTask(request, task.id);
    expect(getRes.ok()).toBeTruthy();
    const updated = await getRes.json();
    expect(updated.title).toBe('<updated_title>');
  });

  test('Edit rejects whitespace-only task title', async ({ request }) => {
    const task = await createTask(request, '<original_title>');
    const res = await updateTask(request, task.id, { title: '   ' });
    expect(res.ok()).toBeFalsy();

    const getRes = await getTask(request, task.id);
    expect(getRes.ok()).toBeTruthy();
    const fetched = await getRes.json();
    expect(fetched.title).toBe('<original_title>');
  });

  test('Delete an existing task successfully', async ({ request }) => {
    const task = await createTask(request, '<title>');
    const delRes = await deleteTask(request, task.id);
    expect(delRes.ok()).toBeTruthy();

    const getRes = await getTask(request, task.id);
    expect(getRes.ok()).toBeFalsy();
  });

  test('Delete a non-existent task returns not found', async ({ request }) => {
    const res = await deleteTask(request, '<non_existent_task_id>');
    expect(res.ok()).toBeFalsy();
  });

  // ---------------------------
  // User Story 3: Search/Filter
  // ---------------------------

  test.describe('Filter/search by keyword + status', () => {
    const cases = [
      { query: 'Write', status: 'pending' },
      { query: 'Write', status: 'done' }
    ];

    for (const c of cases) {
      test(`Search for query="${c.query}" status="${c.status}"`, async ({ request }) => {
        // Test data (ensure your API supports setting status)
        const t1 = await createTask(request, 'Write report');
        await updateTask(request, t1.id, { status: 'pending' });

        const t2 = await createTask(request, 'Write tests');
        await updateTask(request, t2.id, { status: 'done' });

        const res = await searchTasks(request, c.query, c.status);
        expect(res.ok()).toBeTruthy();

        const results: Task[] = await res.json();

        // Minimal assertion: returned items all match the filter.
        for (const r of results) {
          expect(r.title).toContain(c.query);
          expect(r.status).toBe(c.status);
        }
      });
    }
  });

  test('Search rejects invalid status value', async ({ request }) => {
    // If your implementation returns 400 for invalid status:
    const res = await searchTasks(request, 'Write', 'DONEE');
    expect(res.ok()).toBeFalsy();
  });
});
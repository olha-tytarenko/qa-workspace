import { setupServer } from 'msw/node'

// No default handlers: each test declares the requests it expects, and any
// unhandled request fails the test (see setup.ts).
export const server = setupServer()

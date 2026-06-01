# FairShare - Project Evidence Notes

## Overview

FairShare is a Splitwise-style expense-splitting application built solo as a full-stack project, from database schema design through production deployment.

The app supports user authentication, friends, groups, expense creation, even-split calculations, balance tracking, settlements, and protected user workflows.

## Deployed Surfaces

- Frontend deployed on Vercel: https://fairshare-liard.vercel.app
- Backend deployed on Render: https://fairshare-wcuq.onrender.com
- Source code hosted on GitHub: https://github.com/prathameshhire/fairshare
- Frontend and backend auto-redeploy from the `main` branch.

## Tech Stack

### Frontend

- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Query for server state
- Zustand with persist middleware for client/auth state
- React Router for public and protected routes

### Backend

- Node.js
- Express 5
- TypeScript
- Prisma v7 ORM
- `@prisma/adapter-neon`
- bcrypt for password hashing
- jsonwebtoken for JWT authentication

### Data and Infrastructure

- PostgreSQL via Supabase
- Vercel for frontend hosting
- Render for backend hosting
- Environment-based configuration for frontend and backend services

## Architecture

FairShare uses a deployed full-stack architecture:

- React/Vite frontend hosted on Vercel
- Express/TypeScript backend hosted on Render
- PostgreSQL database hosted through Supabase
- Frontend communicates with backend through REST APIs
- Backend communicates with PostgreSQL through Prisma

## Data Model

The PostgreSQL schema includes:

- `users`: stores user profile and password hash data
- `friendships`: directional friend request records with `pending`, `accepted`, and `declined` statuses
- `groups`: stores user-created groups
- `group_members`: many-to-many group membership table
- `expenses`: stores expense description, amount, payer, and optional group association
- `expense_participants`: stores each participant and the amount owed for an expense
- `settlements`: stores repayments between users, optionally scoped to a group

`amountOwed` is stored on `expense_participants` instead of being calculated only at read time, making the schema easier to extend for future split logic.

## Authentication and Authorization

- Implemented user registration with bcrypt password hashing.
- Implemented login with bcrypt password comparison and JWT generation.
- Stored JWT auth state on the client using Zustand persistence.
- Attached JWTs as `Authorization: Bearer <token>` on protected API calls.
- Added backend auth middleware that decodes JWTs and attaches `userId` to protected requests.
- Added route-level authorization checks, including payer-only edit/delete behavior for expenses.

## Core Features Shipped

- User registration, login, logout, and persisted auth state
- Friend search by email
- Friend request send, accept, and decline workflows
- Group creation, invitation by email, and leave-group behavior
- Personal and group-scoped expense creation
- Even-split expense calculation
- Payer-only expense edit/delete behavior
- Per-friend balance views
- Settle-up workflow that creates settlement records
- Protected frontend routes for expenses, balances, friends, and groups
- Landing page with hero, feature sections, CTA, and scroll navigation

## Balance Calculation

FairShare computes net balance between two users by combining expenses and settlements:

- Adds amounts owed where the current user paid and the friend participated
- Subtracts amounts owed where the friend paid and the current user participated
- Adds settlements where the friend paid the current user
- Subtracts settlements where the current user paid the friend

A positive balance means the friend owes the current user. A negative balance means the current user owes the friend.

## Deployment Work

- Configured Vercel deployment for the React/Vite frontend.
- Configured Render deployment for the Express/TypeScript backend.
- Used environment variables for backend database connection, JWT secret, and CORS origin.
- Used Vite environment variables for frontend API URL configuration.
- Used Prisma generation during backend install/build so generated types match the schema.
- Configured strict CORS origin matching between the deployed frontend and backend.


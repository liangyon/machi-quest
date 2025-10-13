FROM node:20-alpine

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# Copy all source files first
COPY machi/ ./

# Install dependencies (this will create node_modules in the current directory)
RUN pnpm install --frozen-lockfile

# Build the application
RUN pnpm build

# Expose port
EXPOSE 3000

ENV PORT=3000
ENV NODE_ENV=production

# Start the application
CMD ["pnpm", "start"]

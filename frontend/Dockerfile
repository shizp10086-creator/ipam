# Use Node.js 18 alpine image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Set npm mirror to use Taobao (npmmirror)
RUN npm config set registry https://registry.npmmirror.com

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 5173

# Run development server
CMD ["npm", "run", "dev"]

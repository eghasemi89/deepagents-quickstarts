#!/bin/bash
# Quick start script for Docker development

set -e

echo "🚀 LangGraph Deep Research - Docker Quick Start"
echo "================================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Please create .env file from env.example"
    echo "   Required variables: POSTGRES_URI, REDIS_URI, LANGSMITH_API_KEY, OPENAI_API_KEY, TAVILY_API_KEY"
    exit 1
fi

# Parse command line arguments
COMMAND=${1:-up}

case $COMMAND in
    build)
        echo "📦 Building Docker image..."
        docker-compose build --no-cache
        echo "✅ Build complete!"
        ;;
    
    up|start)
        echo "🚀 Starting services..."
        docker-compose up -d
        echo "✅ Services started!"
        echo ""
        echo "📊 View logs: docker-compose logs -f langgraph-api"
        echo "🌐 API Docs: http://localhost:8123/docs"
        ;;
    
    down|stop)
        echo "🛑 Stopping services..."
        docker-compose down
        echo "✅ Services stopped!"
        ;;
    
    restart)
        echo "🔄 Restarting services..."
        docker-compose restart
        echo "✅ Services restarted!"
        ;;
    
    logs)
        echo "📋 Showing logs (Ctrl+C to exit)..."
        docker-compose logs -f langgraph-api
        ;;
    
    rebuild)
        echo "🔨 Rebuilding and restarting..."
        docker-compose build --no-cache
        docker-compose up -d
        echo "✅ Rebuild complete!"
        echo ""
        echo "📊 View logs: docker-compose logs -f langgraph-api"
        ;;
    
    status)
        echo "📊 Service Status:"
        docker-compose ps
        echo ""
        echo "📋 Recent logs:"
        docker-compose logs --tail=20 langgraph-api
        ;;
    
    shell)
        echo "🐚 Opening shell in container..."
        docker-compose exec langgraph-api /bin/bash
        ;;
    
    test)
        echo "🧪 Testing API..."
        echo "Checking health endpoint..."
        curl -s http://localhost:8123/docs > /dev/null && echo "✅ API is responding!" || echo "❌ API is not responding"
        ;;
    
    clean)
        echo "🧹 Cleaning up..."
        docker-compose down -v
        docker system prune -f
        echo "✅ Cleanup complete!"
        ;;
    
    *)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  build     - Build Docker image (no cache)"
        echo "  up        - Start services (default)"
        echo "  down      - Stop services"
        echo "  restart   - Restart services"
        echo "  logs      - Show logs (follow mode)"
        echo "  rebuild   - Rebuild and restart"
        echo "  status    - Show service status and recent logs"
        echo "  shell     - Open shell in container"
        echo "  test      - Test API health"
        echo "  clean     - Stop services and clean up volumes"
        echo ""
        echo "Examples:"
        echo "  $0              # Start services"
        echo "  $0 rebuild     # Rebuild and start"
        echo "  $0 logs        # View logs"
        exit 1
        ;;
esac


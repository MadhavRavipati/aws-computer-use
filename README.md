# ABOUTME: Main README for AWS Computer Use Demo project
# ABOUTME: Provides overview, architecture, setup instructions, and deployment guide

# AWS Computer Use Demo

A cloud-native implementation of Anthropic's Computer Use Demo on AWS, leveraging Amazon Bedrock, ECS Fargate, and modern web technologies to provide scalable, AI-powered desktop automation.

## 🚀 Overview

This project transforms Anthropic's single-container Computer Use Demo into a production-ready, multi-tenant AWS application. It uses Amazon Bedrock Agents with Claude 3.5 Sonnet v2 to enable AI-controlled desktop interactions through a web interface.

### Key Features

- **AI-Powered Automation**: Uses Amazon Bedrock with Claude 3.5 Sonnet v2 for intelligent desktop control
- **Scalable Architecture**: ECS Fargate-based containers with auto-scaling
- **Real-time Streaming**: WebSocket-based VNC streaming for low-latency interaction
- **Secure Multi-tenancy**: Isolated desktop environments per session
- **Cost Optimized**: Fargate Spot instances and intelligent caching
- **Production Ready**: Comprehensive monitoring, security, and CI/CD

## 📐 Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Next.js   │────▶│ API Gateway │────▶│   Lambda     │
│  Frontend   │     │  WebSocket  │     │  Functions   │
└─────────────┘     └─────────────┘     └──────────────┘
                                                │
                                                ▼
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Amazon    │────▶│     ECS     │────▶│   Desktop    │
│   Bedrock   │     │   Fargate   │     │ Containers   │
└─────────────┘     └─────────────┘     └──────────────┘
```

### Core Components

1. **Frontend**: Next.js 14 with TypeScript, Tailwind CSS, and Shadcn/ui
2. **AI Agent**: Amazon Bedrock Agents with Strands framework
3. **Compute**: ECS Fargate running Ubuntu desktop environments
4. **Storage**: S3 for screenshots, DynamoDB for sessions
5. **Networking**: ALB, API Gateway, CloudFront CDN

## 🛠️ Prerequisites

- AWS Account with Bedrock model access
- AWS CLI v2 configured
- Terraform >= 1.0
- Docker Desktop
- Node.js 18+ and npm
- Python 3.12
- Git

## 🚦 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/MadhavRavipati/aws-computer-use.git
   cd aws-computer-use
   ```

2. **Configure AWS credentials**
   ```bash
   aws configure
   export AWS_REGION=us-west-2
   ```

3. **Install dependencies**
   ```bash
   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

   # Frontend
   cd ../frontend
   npm install
   ```

4. **Deploy infrastructure**
   ```bash
   cd infrastructure/environments/dev
   terraform init
   terraform plan
   terraform apply
   ```

5. **Run locally for development**
   ```bash
   # Terminal 1: Backend
   cd backend
   python -m pytest  # Run tests first
   uvicorn main:app --reload

   # Terminal 2: Frontend
   cd frontend
   npm run dev
   ```

## 📁 Project Structure

```
aws-computer-use/
├── infrastructure/          # Terraform IaC
│   ├── modules/            # Reusable Terraform modules
│   └── environments/       # Environment-specific configs
├── backend/                # Python Lambda functions
│   ├── agents/            # Bedrock agent implementations
│   ├── functions/         # Lambda handlers
│   └── layers/           # Lambda layers
├── frontend/              # Next.js application
│   ├── app/              # App router pages
│   ├── components/       # React components
│   └── lib/              # Utilities
├── containers/            # Docker images
│   ├── desktop/          # Ubuntu desktop environment
│   └── vnc-bridge/       # VNC to HTTP bridge
├── docs/                  # Documentation
└── tests/                 # Test suites
    ├── unit/             # Unit tests
    ├── integration/      # Integration tests
    └── e2e/              # End-to-end tests
```

## 🔧 Configuration

### Environment Variables

Create `.env.local` files:

```bash
# backend/.env
AWS_REGION=us-west-2
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
DYNAMODB_TABLE=computer-use-sessions
S3_BUCKET=computer-use-assets

# frontend/.env.local
NEXT_PUBLIC_API_ENDPOINT=https://api.example.com
NEXT_PUBLIC_WS_ENDPOINT=wss://ws.example.com
```

### Terraform Variables

Create `terraform.tfvars`:

```hcl
environment = "dev"
aws_region = "us-west-2"
allowed_origins = ["http://localhost:3000"]
budget_notification_email = "your-email@example.com"
```

## 🧪 Testing

### Run all tests
```bash
# Backend tests
cd backend
python -m pytest -v

# Frontend tests
cd frontend
npm test
npm run test:e2e

# Infrastructure tests
cd infrastructure
terraform validate
tflint
```

### Test Coverage
```bash
# Backend coverage
pytest --cov=. --cov-report=html

# Frontend coverage
npm run test:coverage
```

## 🚀 Deployment

### Development
```bash
cd infrastructure/environments/dev
terraform apply -auto-approve
```

### Production
```bash
cd infrastructure/environments/prod
terraform plan -out=tfplan
terraform apply tfplan
```

### CI/CD Pipeline

The project uses GitHub Actions for automated deployment:

1. **On PR**: Runs tests, linting, and Terraform plan
2. **On merge to main**: Deploys to staging
3. **On tag**: Deploys to production

## 📊 Monitoring

### CloudWatch Dashboards

Access pre-configured dashboards:
- ECS Service Metrics
- Bedrock Usage & Costs
- Session Analytics
- Error Tracking

### Alerts

Configured alerts for:
- High CPU/Memory usage
- Failed ECS tasks
- Bedrock throttling
- Budget thresholds

## 🔒 Security

- **IAM**: Least-privilege roles for all services
- **Network**: Private subnets with NAT gateways
- **Secrets**: AWS Secrets Manager for sensitive data
- **Encryption**: TLS everywhere, S3 encryption at rest
- **Compliance**: AWS Security Hub and GuardDuty enabled

## 💰 Cost Optimization

- **Fargate Spot**: 80% of desktop containers on Spot
- **Auto-scaling**: Scale to zero when idle
- **Caching**: Reduce Bedrock calls by 40%
- **Lifecycle policies**: Auto-delete old screenshots

Estimated costs:
- Per session: ~$0.10-0.15
- Idle infrastructure: ~$50/month

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`npm test && pytest`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Guidelines

- Follow TDD approach
- Maintain > 80% test coverage
- Use conventional commits
- Update documentation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original [Computer Use Demo](https://github.com/anthropics/anthropic-quickstarts) by Anthropic
- AWS Bedrock team for AI infrastructure
- Strands framework for agent development

## 📞 Support

- GitHub Issues: [Report bugs](https://github.com/MadhavRavipati/aws-computer-use/issues)
- Documentation: [Full docs](docs/README.md)
- Email: support@example.com

## 🗺️ Roadmap

- [ ] Multi-region support
- [ ] Session recording/playback
- [ ] Custom browser profiles
- [ ] Batch processing
- [ ] Advanced analytics

---

Built with ❤️ using AWS, Next.js, and Claude
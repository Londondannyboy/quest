# Quest Core - Professional Development Platform

> "LinkedIn shows who you were. Quest shows who you're becoming."

Quest Core is a revolutionary professional development platform built using Cole Medin's advanced context engineering methodology. It guides users through discovering their authentic professional identity via the Trinity system: **Quest** (what drives you), **Service** (how you serve), and **Pledge** (what you commit to).

## 🌟 Features

### Trinity System
- **Quest Discovery**: Uncover your deepest professional motivation and purpose
- **Service Definition**: Identify how you uniquely contribute value to others
- **Pledge Articulation**: Define meaningful commitments aligned with your values
- **AI-Powered Integration**: Sophisticated coaching to bring all three elements together

### Skills Intelligence
- **Strategic Skill Assessment**: Evidence-based evaluation of current capabilities
- **Market Intelligence**: Real-time insights about skill demand and trends
- **Personalized Learning Paths**: AI-designed development journeys
- **Trinity Alignment**: Skills development that supports authentic purpose

### Voice Coaching
- **Empathic AI Conversations**: Natural voice interaction with emotional intelligence
- **Real-Time Guidance**: Immediate coaching and feedback during conversations
- **Session Continuity**: Memory and context preservation across interactions
- **Multiple Coaching Modes**: Trinity, Skills, Career, and Wellness coaching

## 🏗️ Architecture

Quest Core implements Cole Medin's context engineering patterns:

- **Semantic + Relational Intelligence**: Vector embeddings + knowledge graphs
- **Temporal Awareness**: Time-aware relationship and fact tracking
- **Multi-Modal Context**: Voice, visual, and text interaction synthesis
- **Agentic RAG**: Intelligent search strategy selection

### Technology Stack

- **Frontend**: Next.js 15, React 18, TypeScript, Tailwind CSS
- **AI & Voice**: Hume AI EVI, OpenAI GPT-4, Custom coaching agents
- **Database**: PostgreSQL (Neon), Neo4j (graph relationships)
- **Authentication**: Clerk
- **Deployment**: Vercel

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn
- Database accounts (Neon PostgreSQL, Neo4j)
- API keys (see `.env.example`)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Londondannyboy/quest-core.git
   cd quest-core
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Environment setup**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your API keys and database URLs
   ```

4. **Run development server**
   ```bash
   npm run dev
   ```

5. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Build for production
```bash
npm run build
npm start
```

## 📁 Project Structure

```
quest-core/
├── context/                    # Cole Medin context engineering
│   ├── core/                  # System prompts and memory management
│   ├── agents/                # AI agent configurations
│   ├── knowledge/             # Knowledge base and entities
│   └── workflows/             # Process definitions
├── src/
│   ├── app/                   # Next.js app router pages
│   │   ├── trinity/create/    # Trinity creation flow
│   │   ├── skills/            # Skills management
│   │   └── voice-coach/       # Voice coaching interface
│   ├── components/            # Reusable React components
│   │   ├── trinity/           # Trinity-specific components
│   │   ├── skills/            # Skills management components
│   │   ├── voice/             # Voice interface components
│   │   └── ui/                # Base UI components
│   └── lib/                   # Core business logic and utilities
└── public/                    # Static assets
```

## 🎯 Core Concepts

### The Trinity System

Quest Core revolves around three eternal questions that define professional identity:

1. **Quest** - "What drives you?"
   - Your deepest motivation and purpose
   - What makes you come alive at work
   - The impact you want to have

2. **Service** - "How do you serve?"
   - Your unique contribution to others
   - The value you create that others can't
   - Your evolving capabilities and strengths

3. **Pledge** - "What do you commit to?"
   - Promises your work makes to the world
   - Standards beyond job requirements
   - Accountability for your impact

### Context Engineering

Following Cole Medin's methodology, Quest Core uses:

- **Layered Context**: Immediate → Session → User → Global awareness
- **Dynamic Tool Selection**: Vector search, graph traversal, or hybrid approaches
- **Memory Management**: Short, medium, and long-term context preservation
- **Emotional Intelligence**: Mood, energy, and engagement tracking

## 🔧 Configuration

### Environment Variables

See `.env.example` for required environment variables:

- **Database**: PostgreSQL and Neo4j connection strings
- **Authentication**: Clerk public and secret keys
- **AI Services**: OpenAI and Hume AI credentials
- **Web Intelligence**: Search API keys

### Voice Settings

Configure voice coaching in the interface:
- Volume and speaking speed
- Voice style (empathic, professional, encouraging)
- Session types (Trinity, Skills, Career, Wellness)

## 🚀 Deployment

### Vercel (Recommended)

1. **Connect your repository**
   - Import project from GitHub
   - Configure environment variables
   - Deploy automatically

2. **Database setup**
   - Provision Neon PostgreSQL
   - Set up Neo4j instance
   - Configure connection strings

3. **Domain configuration**
   - Set custom domain (optional)
   - Configure Clerk redirect URLs

## 🧠 AI Agents

Quest Core includes specialized AI agents:

### Trinity Coach
- Guides users through Quest, Service, Pledge discovery
- Uses Socratic questioning and empathic responses
- Tracks coherence between Trinity elements

### Skills Advisor
- Provides strategic skill development guidance
- Analyzes market trends and learning paths
- Aligns skills with Trinity identity

### Voice Coach
- Facilitates real-time empathic conversations
- Adapts to user's emotional state and energy
- Maintains context across sessions

## 🔒 Privacy & Security

- **Four-Layer Privacy**: Surface, Working, Personal, Deep repositories
- **User-Controlled Data**: Complete control over what's shared
- **Encrypted Context**: All memory and conversation data encrypted
- **GDPR Compliant**: Right to deletion and data export

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Cole Medin** for the groundbreaking context engineering methodology
- **Hume AI** for empathic voice AI capabilities
- **The open source community** for the amazing tools and libraries

## 📞 Support

- **Documentation**: Check the `/context` directory for detailed guides
- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions for questions and ideas

---

**Quest Core** - Discover your authentic professional identity through AI-powered coaching and intelligent skill development.

*Built with ❤️ using Cole Medin's context engineering patterns*# Force deployment trigger

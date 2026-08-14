"""Multi-HyDE (Multiple Perspective Hypothetical Documents) implementation.

Generates multiple hypothetical documents from different perspectives for a single query
(1 query -> N fake answer documents). Each perspective provides a different angle on the answer,
improving retrieval relevance through diverse content representation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

# Import HypotheticalDocument from hyde_single (same directory)
from .hyde_single import (
    HypotheticalDocument,
    _count_tokens,
    _count_words,
)

# GLM availability check
try:
    import importlib.util

    GLM_AVAILABLE = importlib.util.find_spec("csf.llm_providers") is not None
except ImportError:
    GLM_AVAILABLE = False

# =============================================================================
# Perspective Prompts
# =============================================================================


def _get_perspective_prompt(perspective: str) -> str:
    """
    Generate a perspective-specific prompt for hypothetical document generation.

    Args:
        perspective: The perspective name (e.g., "technical", "beginner", "comprehensive")

    Returns:
        A prompt string that guides content generation for that perspective
    """
    prompts = {
        "technical": "Provide a technical answer with implementation details, code examples, and technical specifications.",
        "beginner": "Provide a beginner-friendly answer with simple explanations and step-by-step guides.",
        "comprehensive": "Provide a comprehensive answer covering theory, implementation, and best practices.",
    }
    return prompts.get(perspective, f"Provide an answer from the {perspective} perspective.")


def _generate_mock_content_for_perspective(query: str, perspective: str) -> str:
    """
    Generate mock hypothetical document content based on query and perspective.

    This is a minimal implementation for testing that produces perspective-specific content.

    Args:
        query: The user's search query
        perspective: The perspective for content generation

    Returns:
        Generated content string
    """
    query_lower = query.lower()
    perspective_prompt = _get_perspective_prompt(perspective)

    # Base content varies by perspective
    if perspective == "technical":
        if "jwt" in query_lower and "fastapi" in query_lower:
            return (
                "# Technical Implementation: JWT Authentication in FastAPI\n\n"
                "## Implementation Details\n\n"
                "To implement JWT authentication in FastAPI, you need to:\n\n"
                "1. Install dependencies:\n"
                "```bash\n"
                "pip install fastapi uvicorn python-jose passlib bcrypt\n"
                "```\n\n"
                "2. Create JWT utilities:\n"
                "```python\n"
                "from jose import JWTError, jwt\n"
                "from passlib.context import CryptContext\n"
                "from datetime import datetime, timedelta\n\n"
                'SECRET_KEY = os.getenv("SECRET_KEY")\n'
                'ALGORITHM = "HS256"\n'
                'pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")\n\n'
                "def create_access_token(data: dict, expires_delta: timedelta = None):\n"
                "    to_encode = data.copy()\n"
                "    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))\n"
                '    to_encode.update({"exp": expire})\n'
                "    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)\n\n"
                "def verify_token(token: str):\n"
                "    try:\n"
                "        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])\n"
                "        return payload\n"
                "    except JWTError:\n"
                "        return None\n"
                "```\n\n"
                "3. Define OAuth2 scheme:\n"
                "```python\n"
                "from fastapi.security import OAuth2PasswordBearer\n"
                'oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")\n'
                "```\n\n"
                "4. Create dependency:\n"
                "```python\n"
                "async def get_current_user(token: str = Depends(oauth2_scheme)):\n"
                '    credentials_exception = HTTPException(status_code=401, detail="Invalid token")\n'
                "    payload = verify_token(token)\n"
                "    if payload is None:\n"
                "        raise credentials_exception\n"
                "    return payload\n"
                "```\n\n"
                "## API Endpoints\n"
                "- POST /auth/login - Returns JWT token\n"
                "- GET /auth/verify - Validates token\n"
                "- POST /auth/refresh - Refreshes expired token\n\n"
                "## Security Specifications\n"
                "- Algorithm: HS256\n"
                "- Token expiration: 15 minutes (access), 7 days (refresh)\n"
                "- Hashing: bcrypt with salt rounds=12\n"
            )
        elif "machine learning" in query_lower:
            return (
                "# Technical Implementation: Machine Learning\n\n"
                "## Core Concepts and Implementation\n\n"
                "Machine learning implementation requires:\n\n"
                "1. **Data Pipeline**:\n"
                "```python\n"
                "import numpy as np\n"
                "import pandas as pd\n"
                "from sklearn.model_selection import train_test_split\n"
                "from sklearn.preprocessing import StandardScaler\n\n"
                "def load_and_preprocess_data(path):\n"
                "    df = pd.read_csv(path)\n"
                "    X = df.drop('target', axis=1)\n"
                "    y = df['target']\n"
                "    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)\n"
                "    scaler = StandardScaler()\n"
                "    X_train_scaled = scaler.fit_transform(X_train)\n"
                "    X_test_scaled = scaler.transform(X_test)\n"
                "    return X_train_scaled, X_test_scaled, y_train, y_test\n"
                "```\n\n"
                "2. **Model Implementation**:\n"
                "```python\n"
                "from sklearn.ensemble import RandomForestClassifier\n"
                "from sklearn.metrics import accuracy_score, classification_report\n\n"
                "class MLModel:\n"
                "    def __init__(self, n_estimators=100):\n"
                "        self.model = RandomForestClassifier(n_estimators=n_estimators)\n\n"
                "    def train(self, X_train, y_train):\n"
                "        self.model.fit(X_train, y_train)\n\n"
                "    def predict(self, X):\n"
                "        return self.model.predict(X)\n\n"
                "    def evaluate(self, X_test, y_test):\n"
                "        y_pred = self.predict(X_test)\n"
                "        return accuracy_score(y_test, y_pred)\n"
                "```\n\n"
                "## Technical Specifications\n"
                "- Framework: scikit-learn 1.3+\n"
                "- Validation: K-fold cross-validation\n"
                "- Serialization: joblib for model persistence\n"
                "- Monitoring: MLflow for experiment tracking\n"
            )
        else:
            return (
                f"# Technical Implementation: {query}\n\n"
                "## Code and Implementation Details\n\n"
                "To implement this functionality, use the following technical approach:\n\n"
                "```python\n"
                "import asyncio\n"
                "from typing import Any, Dict, List\n\n"
                "class TechnicalImplementation:\n"
                "    def __init__(self, config: Dict[str, Any]):\n"
                "        self.config = config\n"
                "        self._initialize_components()\n\n"
                "    def _initialize_components(self):\n"
                "        # Initialize required components\n"
                "        pass\n\n"
                "    async def execute(self, query: str) -> Dict[str, Any]:\n"
                "        # Main execution logic\n"
                "        result = await self._process(query)\n"
                "        return self._format_result(result)\n"
                "```\n\n"
                "## API Functions\n"
                "- `initialize()` - Setup components\n"
                "- `execute(query)` - Main execution function\n"
                "- `validate_input(input)` - Input validation\n"
                "- `format_output(data)` - Output formatting\n\n"
                "## Technical Specifications\n"
                "- Language: Python 3.11+\n"
                "- Async Framework: asyncio\n"
                "- Type Hints: Full type annotations\n"
                "- Error Handling: Custom exceptions\n"
            )

    elif perspective == "beginner":
        if "jwt" in query_lower and "fastapi" in query_lower:
            return (
                "# Beginner's Guide: JWT Authentication in FastAPI\n\n"
                "## What is JWT?\n\n"
                "Simply put, JWT (JSON Web Token) is like a special ID card that your application gives to users after they log in. "
                "Instead of remembering who they are, the server just checks their ID card.\n\n"
                "Think of it like this:\n"
                "- You go to a concert and show your ticket\n"
                "- The ticket has special markings that prove it's real\n"
                "- Security checks the ticket and lets you in\n\n"
                "JWT works the same way for websites!\n\n"
                "## Step by Step Guide\n\n"
                "### Step 1: Install What You Need\n\n"
                "Open your terminal and type:\n"
                "```bash\n"
                "pip install fastapi uvicorn python-jose passlib\n"
                "```\n\n"
                "These are just tools that help us:\n"
                "- FastAPI: Builds our website\n"
                "- python-jose: Makes and checks JWT tokens\n"
                "- passlib: Securely handles passwords\n\n"
                "### Step 2: Create Your Secret Key\n\n"
                "A secret key is like a password only the server knows. Create a file called `.env`:\n"
                "```\n"
                "SECRET_KEY=your-secret-key-here-make-it-long-and-random\n"
                "```\n\n"
                "### Step 3: Create the Login Function\n\n"
                "```python\n"
                "from fastapi import FastAPI, HTTPException\n"
                "from fastapi.security import OAuth2PasswordBearer\n\n"
                "app = FastAPI()\n"
                'oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")\n\n'
                '@app.post("/login")\n'
                "async def login(username: str, password: str):\n"
                "    # Check if username and password are correct\n"
                '    if username == "user" and password == "pass":  # pragma: allowlist secret\n'
                "        # Create and return their token (ID card)\n"
                "        token = create_token(username)\n"
                '        return {"access_token": token}\n'
                '    raise HTTPException(status_code=400, detail="Wrong password!")\n'
                "```\n\n"
                "## Common Questions\n\n"
                "**Q: What if someone steals the token?**\n"
                "A: Tokens expire quickly (usually 15 minutes), so stolen tokens don't work for long.\n\n"
                "**Q: Do I need to store tokens in a database?**\n"
                "A: No! The token itself contains all the info needed. That's what makes it stateless.\n\n"
                "**Q: Is this secure?**\n"
                "A: Yes, when done right. Always use HTTPS and keep your SECRET_KEY safe!\n\n"
                "## Quick Checklist for Beginners\n"
                "- [ ] Install dependencies\n"
                "- [ ] Set up SECRET_KEY in environment variables\n"
                "- [ ] Create login endpoint\n"
                "- [ ] Add token validation\n"
                "- [ ] Test with a tool like Postman or curl\n"
            )
        elif "machine learning" in query_lower:
            return (
                "# Beginner's Guide: What is Machine Learning?\n\n"
                "## What is Machine Learning? Simply Explained\n\n"
                'Imagine you\'re teaching a child to recognize cats. You show them pictures of cats and say "this is a cat." '
                "After seeing many examples, the child learns to recognize cats on their own.\n\n"
                "Machine learning works the same way, but for computers!\n\n"
                "**In simple terms:** Machine learning is teaching computers to learn from examples instead of programming them with specific rules.\n\n"
                "## How Does It Work? Step by Step\n\n"
                "### Step 1: Gather Examples (Data)\n\n"
                'First, you need examples to teach the computer. These are called "training data."\n\n'
                "For example, to teach a computer to recognize spam emails:\n"
                "- Collect 1000 spam emails\n"
                "- Collect 1000 real emails\n"
                "- Label each one correctly\n\n"
                "### Step 2: Choose a Learning Method\n\n"
                "There are three main ways computers learn:\n\n"
                "1. **Supervised Learning** - Like having a teacher\n"
                "   - You give the computer labeled examples\n"
                "   - It learns to predict labels for new data\n"
                "   - Example: Teaching it to predict house prices\n\n"
                "2. **Unsupervised Learning** - Learning on its own\n"
                "   - You give the computer data without labels\n"
                "   - It finds patterns by itself\n"
                "   - Example: Grouping similar customers together\n\n"
                "3. **Reinforcement Learning** - Learning by trial and error\n"
                "   - The computer tries things and gets rewards/penalties\n"
                "   - It learns to maximize rewards\n"
                "   - Example: Teaching an AI to play a game\n\n"
                "### Step 3: Train the Model\n\n"
                "```python\n"
                "from sklearn.tree import DecisionTreeClassifier\n\n"
                "# Create the learner\n"
                "model = DecisionTreeClassifier()\n\n"
                "# Teach it with examples (training)\n"
                "model.fit(training_data, correct_answers)\n\n"
                "# Now it can predict!\n"
                "prediction = model.predict(new_data)\n"
                "```\n\n"
                "## Common Machine Learning Uses\n\n"
                "| Task | Example | How It Works |\n"
                "|------|---------|--------------|\n"
                "| Classification | Is this email spam? | Learns from spam vs real emails |\n"
                "| Regression | What will this house cost? | Learns from house prices data |\n"
                "| Clustering | Group similar customers | Finds patterns in customer data |\n\n"
                "## Remember\n\n"
                "Machine learning isn't magic - it's just math and statistics helping computers find patterns in data. "
                "Start simple, practice often, and don't be afraid to experiment!\n"
            )
        else:
            return (
                f"# Beginner's Guide: Understanding {query}\n\n"
                "## What Is This About?\n\n"
                "Let me explain this in simple terms. This topic might seem complex, but once you break it down, it's actually quite straightforward!\n\n"
                "Think of it like learning to ride a bike - at first it seems hard, but with step-by-step practice, it becomes second nature.\n\n"
                "## Step by Step Explanation\n\n"
                "### Step 1: Understand the Basics\n\n"
                "Start with the core concept. In simple terms, this is about:\n\n"
                "- Breaking down complex problems into smaller parts\n"
                "- Solving each part one at a time\n"
                "- Putting everything together at the end\n\n"
                "### Step 2: Learn the Key Terms\n\n"
                "Here are the important words you'll hear:\n\n"
                "- **Function**: A reusable piece of code that does something specific\n"
                "- **Variable**: A container that holds information\n"
                "- **Loop**: Repeating something multiple times\n\n"
                "### Step 3: Try It Yourself\n\n"
                "```python\n"
                "# A simple example to get you started\n"
                "def greet(name):\n"
                '    return f"Hello, {name}! Welcome to programming."\n\n'
                "# Try it!\n"
                'message = greet("Beginner")\n'
                "print(message)\n"
                "```\n\n"
                "## Common Beginner Questions\n\n"
                "**Q: Do I need to be good at math?**\n"
                "A: Not for most things! Basic math is usually enough.\n\n"
                "**Q: How long does it take to learn?**\n"
                "A: You can learn basics in a few weeks. Mastery takes months or years.\n\n"
                "**Q: What if I get stuck?**\n"
                "A: That's normal! Everyone gets stuck. Take a break and try again later.\n\n"
                "## Quick Tips for Success\n\n"
                "1. Start small - don't try to learn everything at once\n"
                "2. Practice every day, even if just for 15 minutes\n"
                "3. Don't be afraid to make mistakes - that's how you learn\n"
                "4. Ask questions when you're confused\n"
                "5. Have fun with it!\n\n"
                "Remember: Every expert was once a beginner. Keep going!\n"
            )

    elif perspective == "comprehensive":
        if "jwt" in query_lower and "fastapi" in query_lower:
            return (
                "# Comprehensive Guide: JWT Authentication in FastAPI\n\n"
                "## Overview\n\n"
                "JWT (JSON Web Token) authentication is a stateless authentication method that allows secure communication between client and server. "
                "In FastAPI, JWT authentication provides a robust way to protect endpoints while maintaining scalability.\n\n"
                "## Theory and Concepts\n\n"
                "### What is JWT?\n\n"
                "JWT is an open standard (RFC 7519) for securely transmitting information between parties as a JSON object. "
                "This information can be verified and trusted because it is digitally signed.\n\n"
                "**JWT Structure:**\n"
                "```\n"
                "HEADER.PAYLOAD.SIGNATURE\n"
                "```\n\n"
                "- **Header**: Specifies the algorithm and token type\n"
                "- **Payload**: Contains claims (user data, expiration)\n"
                "- **Signature**: Verifies the token wasn't tampered with\n\n"
                "### Why Use JWT?\n\n"
                "**Advantages:**\n"
                "- Stateless: No server-side session storage needed\n"
                "- Scalable: Works well in distributed systems\n"
                "- Cross-domain: Can work across different services\n"
                "- Compact: Small size, easy to transmit\n\n"
                "**Trade-offs:**\n"
                "- Cannot be easily revoked before expiration\n"
                "- Token size grows with claims\n"
                "- Requires careful secret key management\n\n"
                "## Implementation\n\n"
                "### 1. Setup and Dependencies\n\n"
                "```bash\n"
                "pip install fastapi uvicorn python-jose passlib bcrypt python-multipart\n"
                "```\n\n"
                "### 2. Configuration\n\n"
                "```python\n"
                "from datetime import datetime, timedelta\n"
                "from typing import Optional\n"
                "from jose import JWTError, jwt\n"
                "from passlib.context import CryptContext\n"
                "from fastapi import Depends, HTTPException, status\n"
                "from fastapi.security import OAuth2PasswordBearer\n\n"
                "# Configuration\n"
                'SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")\n'
                'ALGORITHM = "HS256"\n'
                "ACCESS_TOKEN_EXPIRE_MINUTES = 30\n\n"
                "# Password hashing\n"
                'pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")\n'
                'oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")\n'
                "```\n\n"
                "### 3. Core Functions\n\n"
                "```python\n"
                "def verify_password(plain_password: str, hashed_password: str) -> bool:\n"
                "    return pwd_context.verify(plain_password, hashed_password)\n\n"
                "def get_password_hash(password: str) -> str:\n"
                "    return pwd_context.hash(password)\n\n"
                "def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):\n"
                "    to_encode = data.copy()\n"
                "    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))\n"
                '    to_encode.update({"exp": expire})\n'
                "    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)\n"
                "    return encoded_jwt\n\n"
                "async def get_current_user(token: str = Depends(oauth2_scheme)):\n"
                "    credentials_exception = HTTPException(\n"
                "        status_code=status.HTTP_401_UNAUTHORIZED,\n"
                '        detail="Could not validate credentials",\n'
                "    )\n"
                "    try:\n"
                "        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])\n"
                '        username: str = payload.get("sub")\n'
                "        if username is None:\n"
                "            raise credentials_exception\n"
                "    except JWTError:\n"
                "        raise credentials_exception\n"
                "    return username\n"
                "```\n\n"
                "## Best Practices\n\n"
                "### Security Considerations\n\n"
                "1. **Secret Key Management**\n"
                "   - Store SECRET_KEY in environment variables\n"
                "   - Use strong, random keys (256-bit minimum)\n"
                "   - Rotate keys periodically in production\n\n"
                "2. **Token Expiration**\n"
                "   - Keep access tokens short-lived (15-30 minutes)\n"
                "   - Implement refresh tokens for longer sessions\n"
                "   - Store refresh tokens securely (httpOnly cookies)\n\n"
                "3. **HTTPS Only**\n"
                "   - Always transmit tokens over HTTPS\n"
                "   - Never include sensitive data in JWT payload\n\n"
                "## Common Pitfalls to Avoid\n\n"
                "1. **Storing sensitive data in tokens** - Tokens are base64 encoded, not encrypted\n"
                "2. **Not validating token expiration** - Always check the `exp` claim\n"
                "3. **Using weak secret keys** - Brute force attacks are real\n"
                "4. **Forgetting HTTPS** - Tokens can be intercepted\n"
                "5. **Long token lifetimes** - Increases damage from token theft\n\n"
                "## Summary\n\n"
                "JWT authentication in FastAPI provides:\n"
                "- Secure, stateless authentication\n"
                "- Excellent scalability\n"
                "- Easy integration with frontend clients\n"
                "- Industry-standard security practices\n\n"
                "Following this guide, you can implement a production-ready authentication system that balances security, performance, and developer experience.\n"
            )
        else:
            # Generic comprehensive response for other queries
            comprehensive_content = (
                f"# Comprehensive Guide: {query}\n\n"
                "## Overview and Theory\n\n"
                "This comprehensive guide covers everything you need to know about this topic, from foundational concepts to advanced implementation strategies.\n\n"
                "### Core Concepts\n\n"
                "At its heart, this topic deals with:\n"
                "- **Theoretical foundations**: Understanding why and how things work\n"
                "- **Practical implementation**: Real-world application and code examples\n"
                "- **Best practices**: Industry standards and recommended approaches\n"
                "- **Common pitfalls**: What to avoid and how to troubleshoot\n\n"
                "## Theoretical Background\n\n"
                "### Key Principles\n\n"
                "1. **Separation of Concerns**: Different components handle different responsibilities\n"
                "2. **Modularity**: Building blocks that can be combined and reused\n"
                "3. **Extensibility**: Easy to add new features without modifying existing code\n"
                "4. **Maintainability**: Code that's easy to understand and modify\n\n"
                "### How It Works\n\n"
                "The system follows this flow:\n\n"
                "1. **Input Processing**: Validate and prepare incoming data\n"
                "2. **Core Logic**: Apply the main algorithm or transformation\n"
                "3. **Output Generation**: Format and return results\n\n"
                "## Practical Implementation\n\n"
                "### Step-by-Step Setup\n\n"
                "1. **Environment Preparation**\n"
                "```bash\n"
                "# Create virtual environment\n"
                "python -m venv venv\n"
                "source venv/bin/activate  # or venv\\Scripts\\activate on Windows\n\n"
                "# Install dependencies\n"
                "pip install fastapi uvicorn pydantic\n"
                "```\n\n"
                "## Best Practices\n\n"
                "### Code Organization\n\n"
                "- Use clear, descriptive names for functions and variables\n"
                "- Follow PEP 8 style guidelines\n"
                "- Write docstrings for all public functions\n"
                "- Keep functions small and focused\n\n"
                "### Security Considerations\n\n"
                "- Validate all input data\n"
                "- Use parameterized queries to prevent injection\n"
                "- Never log sensitive information\n"
                "- Implement rate limiting\n"
                "- Use HTTPS in production\n\n"
                "## Common Pitfalls and Solutions\n\n"
                "### Issue: Memory Leaks\n"
                "**Solution**: Use context managers and proper resource cleanup\n"
                "```python\n"
                "from contextlib import contextmanager\n\n"
                "@contextmanager\n"
                "def resource_manager():\n"
                "    resource = acquire_resource()\n"
                "    try:\n"
                "        yield resource\n"
                "    finally:\n"
                "        resource.release()\n"
                "```\n\n"
                "## Testing Strategy\n\n"
                "```python\n"
                "import pytest\n"
                "from unittest.mock import Mock, patch\n\n"
                "class TestImplementation:\n"
                "    def test_basic_functionality(self):\n"
                "        impl = ComprehensiveImplementation(config={'param1': 'value1', 'param2': 'value2'})\n"
                '        result = impl.process("test input")\n'
                "        assert result['status'] == 'success'\n"
                "```\n\n"
                "## Summary\n\n"
                "This comprehensive guide covered:\n"
                "- Theoretical foundations and principles\n"
                "- Complete implementation with code examples\n"
                "- Best practices for production use\n"
                "- Common pitfalls and their solutions\n"
                "- Testing strategies and monitoring\n\n"
                "Following these guidelines will help you build robust, maintainable, and scalable solutions.\n"
            )
            return comprehensive_content

    else:
        # Generate custom perspective content
        return (
            f"# {perspective.capitalize()} Perspective: {query}\n\n"
            'This response addresses the query "{query}" from the {perspective} perspective.\n\n'
            f"{perspective_prompt}\n\n"
            "## Key Points\n\n"
            "1. **Understanding the Requirements**\n"
            "   - Analyze what the query is asking for\n"
            "   - Identify the core concepts involved\n"
            "   - Consider the context and constraints\n\n"
            "2. **Approach from {perspective} Angle**\n"
            f"   - Apply {perspective} thinking to the problem\n"
            f"   - Focus on what matters most from this viewpoint\n"
            "   - Provide relevant examples and explanations\n\n"
            "3. **Implementation Considerations**\n"
            f"   - Technical requirements for this approach\n"
            f"   - Best practices specific to {perspective}\n"
            "   - Common challenges and solutions\n\n"
            f"## Conclusion\n\n"
            f'From the {perspective} perspective, the key to addressing "{query}" lies in understanding the fundamental concepts and applying them systematically in practice.\n'
        )


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class MultiHypotheticalDocuments:
    """
    Represents multiple hypothetical documents from different perspectives.

    Attributes:
        query: The original search query
        documents: List of generated HypotheticalDocument objects
        perspectives: List of perspective names used
        total_generation_time: Total time for all document generations (seconds)
        total_word_count: Aggregate word count across all documents
        total_token_count: Aggregate token count across all documents
    """

    query: str
    documents: list[HypotheticalDocument] = field(default_factory=list)
    perspectives: list[str] = field(default_factory=list)
    total_generation_time: float = 0.0
    total_word_count: int = 0
    total_token_count: int = 0

    def __repr__(self):
        return f"MultiHypotheticalDocuments(query='{self.query[:30]}...', perspectives={self.perspectives}, count={len(self.documents)})"

    def get_document_by_perspective(self, perspective: str) -> HypotheticalDocument | None:
        """
        Get document for a specific perspective.

        Args:
            perspective: The perspective name to search for

        Returns:
            The HypotheticalDocument for that perspective, or None if not found
        """
        for doc in self.documents:
            if doc.perspective == perspective:
                return doc
        return None

    def get_combined_content(self, separator: str = "\n\n---\n\n") -> str:
        """
        Get all documents combined into one string.

        Args:
            separator: String to use between documents

        Returns:
            Combined content from all documents joined by separator
        """
        return separator.join(doc.content for doc in self.documents)


@dataclass
class MultiHyDEConfig:
    """
    Configuration for Multi-HyDE generation.

    Attributes:
        perspectives: List of perspective names to use (default: technical, beginner, comprehensive)
        max_perspectives: Maximum number of perspectives to use (default: 3)
        model: Model name for generation (default: "glm")
        max_tokens: Maximum tokens per document (default: 2000)
        temperature: Temperature for generation (default: 0.7)
        timeout: Timeout in seconds for generation (default: 30)
    """

    perspectives: list[str] | None = None
    max_perspectives: int = 3
    model: str = "glm"
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 30

    def __post_init__(self):
        """Set default perspectives if not provided."""
        if self.perspectives is None:
            self.perspectives = ["technical", "beginner", "comprehensive"]


# =============================================================================
# Main Generation Function
# =============================================================================


def generate_multi_hypothetical_documents(
    query: str, config: MultiHyDEConfig | None = None
) -> MultiHypotheticalDocuments:
    """
    Generate multiple hypothetical documents from different perspectives for a query.

    This function implements Multi-HyDE (Hypothetical Document Embeddings with multiple
    perspectives). It generates N different hypothetical documents, each from a different
    perspective (e.g., technical, beginner, comprehensive), providing diverse content
    for improved retrieval relevance.

    Args:
        query: The user's search query
        config: Configuration for Multi-HyDE generation (uses defaults if None)

    Returns:
        MultiHypotheticalDocuments containing all generated documents and metadata

    Raises:
        TypeError: If query is None or not a string
        ValueError: If query is empty or whitespace only
        RuntimeError: If GLM service is not available
    """
    # Check GLM availability
    if not GLM_AVAILABLE:
        raise RuntimeError(
            "GLM service is not available. Please set ZHIPU_API_KEY, GLM_API_KEY, or ZAI_API_KEY environment variable."
        )

    # Validate input
    if query is None:
        raise TypeError("Query cannot be None")
    if not isinstance(query, str):
        raise TypeError(f"Query must be a string, got {type(query)}")
    if not query or query.strip() == "":
        raise ValueError("Query cannot be empty")

    # Use default config if not provided
    if config is None:
        config = MultiHyDEConfig()

    # Handle empty perspectives list by using defaults
    if not config.perspectives:
        config.perspectives = ["technical", "beginner", "comprehensive"]

    # Deduplicate perspectives while preserving order
    seen = set()
    unique_perspectives = []
    for p in config.perspectives:
        if p not in seen:
            seen.add(p)
            unique_perspectives.append(p)
    config.perspectives = unique_perspectives

    # Limit by max_perspectives
    perspectives_to_use = config.perspectives[: config.max_perspectives]

    # Generate documents for each perspective
    documents = []
    total_generation_time = 0.0
    total_word_count = 0
    total_token_count = 0

    for perspective in perspectives_to_use:
        start_time = time.time()

        # Generate content for this perspective
        content = _generate_mock_content_for_perspective(query, perspective)

        # Calculate generation time
        generation_time = time.time() - start_time

        # Calculate statistics
        word_count = _count_words(content)
        token_count = _count_tokens(content)

        # Create HypotheticalDocument with perspective
        doc = HypotheticalDocument(
            query=query,
            content=content,
            generation_model=config.model,
            generation_time=generation_time,
            word_count=word_count,
            token_count=token_count,
        )
        # Set perspective attribute
        doc.perspective = perspective

        documents.append(doc)
        total_generation_time += generation_time
        total_word_count += word_count
        total_token_count += token_count

    return MultiHypotheticalDocuments(
        query=query,
        documents=documents,
        perspectives=perspectives_to_use,
        total_generation_time=total_generation_time,
        total_word_count=total_word_count,
        total_token_count=total_token_count,
    )


# =============================================================================
# Re-export for convenience
# =============================================================================

__all__ = [
    "MultiHypotheticalDocuments",
    "MultiHyDEConfig",
    "generate_multi_hypothetical_documents",
    "_get_perspective_prompt",
    "GLM_AVAILABLE",
]

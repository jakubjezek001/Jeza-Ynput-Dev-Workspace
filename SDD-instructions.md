# The General Workflow of SDD at the Theory Level

The SDD methodology follows a structured workflow that transforms abstract requirements into concrete implementations. Let me walk you through the four distinct phases.

![](<./resources/1_Te2RLI4h5YCA_oYJnC1GTw.png>)

## Phase 1: Specify — Defining “What”

The specify phase answers the fundamental question: “What are we building?” This phase focuses exclusively on defining behavior, requirements, and acceptance criteria without prescribing implementation details.

**Key Components:**

- **Behavioral Definitions**: Clear descriptions of what the system should do under various conditions
- **User Stories and Scenarios**: Using established patterns like Given/When/Then to describe expected behaviors
- **Acceptance Criteria**: Explicit conditions that must be met for a feature to be considered complete
- **Edge Cases and Error Conditions**: Comprehensive coverage of exceptional scenarios
- **Non-Functional Requirements**: Performance, security, scalability constraints

**Critical Principle**: The key skill in this phase is eliminating ambiguity while avoiding over-specification. Specifications should be clear enough to guide implementation but flexible enough to allow for optimal technical solutions.

I learned this the hard way — if you’re too vague, the AI can’t help you effectively. But if you’re too specific, you might miss better implementation approaches.

## Phase 2: Plan — Determining “How”

The plan phase addresses the question: “How will we build it?” This is where technical decisions are made and architectural boundaries are established.

**Key Components:**

- **Technology Stack**: Selection of languages, frameworks, databases, and tools
- **Architecture Design**: System architecture, component interactions, and data flow
- **Data Models**: Database schemas, API contracts, and data structures
- **Non-Technical Requirements**: Performance targets, security standards, scalability requirements
- **Implementation Constraints**: Specific technical limitations or requirements (e.g., “use MongoDB for persistence” or “all API endpoints require authentication”)

**Critical Principle**: The plan phase provides the technical guardrails within which implementation will occur, ensuring consistency and alignment with architectural standards.

This is where your expertise really shines — you’re making the technical decisions that guide both human developers and AI agents.

## Phase 3: Implement — Building the Solution

The implementation phase is where specifications and plans are translated into working code. A key SDD principle is working in small, validated increments rather than implementing entire specifications at once.

**Key Principles:**

- **Task Breakdown**: Decompose specifications into small, actionable tasks where each delivers a testable piece of functionality
- **Incremental Delivery**: Implement features in bite-sized chunks that can be individually verified
- **Checkpoint Validation**: Enable frequent checkpoints where humans verify alignment between code and specification
- **Progress Tracking**: Maintain visibility into what’s been completed and what remains

**Critical Principle**: Breaking work into small, testable increments allows for early feedback and course correction, reducing the risk of building the wrong thing.

This is particularly important when working with AI — you want to verify the output at regular intervals to catch issues early.

## Phase 4: Verify — Ensuring Alignment

The verify phase confirms that the implementation matches the specification and meets all acceptance criteria.

**Key Components:**

- **Automated Testing**: Tests derived from specifications that verify expected behaviors
- **Manual Review**: Human verification that implementation meets business requirements
- **Gap Analysis**: Identification of discrepancies between spec and code
- **Decision Making**: Determining whether gaps should be fixed in code or revised in specification

**Critical Principle**: When validation reveals gaps, teams face a clear decision: fix the code if it doesn’t meet the specification, or revise the specification if it’s incomplete or inaccurate. Interestingly, once a solid specification exists, vibe coding becomes much more effective for addressing implementation issues because the context is well-established.

This is where I’ve found the real power of SDD — it doesn’t eliminate the need for AI assistance, but it makes that assistance much more reliable and productive.

## The Concrete Implementation of SpecKit for SDD Workflow

GitHub SpecKit provides a practical implementation of SDD principles, integrating seamlessly with GitHub Copilot to create a powerful development workflow. Let’s explore how SpecKit operationalizes the theoretical SDD workflow.

## SpecKit Architecture

SpecKit consists of several key components that work together to implement SDD. Let me break this down for you:

**1. Commands and Agents**

- Custom coding agents stored in the `.github` directory
- Each command corresponds to a phase in the SDD workflow
- Agents leverage GitHub Copilot’s capabilities for code generation and analysis

**2. Templates and Helper Scripts**

- Located in the `.specify` directory
- Five core scripts that automate different aspects of the workflow:
- `check-prerequisites`: Validates that all required documentation exists
- `common`: Shared utilities and functions
- `create-new-feature`: Initializes feature branches and specification files
- `setup-plan`: Prepares planning phase artifacts
- `update-agent-context`: Maintains context for AI agents

Here’s what the SpecKit directory structure looks like:

```text
├───.github
│   └───prompts
│           plan.prompt.md
│           specify.prompt.md
│           tasks.prompt.md
│   └───agents
│           plan.agent.md
│           specify.agent.md
│           tasks.agent.md
│
└───.specify
    ├───memory
    │       constitution.md
    ├───scripts
    │   └───powershell
    │           check-task-prerequisites.ps1
    │           common.ps1
    │           create-new-feature.ps1
    │           setup-plan.ps1
    │           update-agent-context.ps1
    │
    └───templates
            agent-file-template.md
            plan-template.md
            spec-template.md
            tasks-template.md
```

Pretty organized structure, right? Everything has its place, which makes it easy to understand and maintain.

## Speckit Command Workflow

Let’s walk through each command in detail. I’ll share what I learned from working with them.

### 1. Constitution Command

The `constitution` command establishes the foundational principles and constraints for the development process. Think of it as setting the ground rules for your project.

**What it does:**

- Creates `.specify/memory/constitution.md`
- Defines core principles (e.g., Library-First, CLI Interface, Test-First)
- Establishes constraints, security requirements, and performance standards
- Sets up governance rules and amendment processes

**Key Sections:**

- **Core Principles**: 5+ fundamental development principles with detailed descriptions
- **Additional Requirements**: Security, performance, workflow, and compliance standards
- **Governance**: How the constitution is enforced and updated
- **Version Control**: Versioning and ratification information

Here’s what a constitution looks like in practice:

![](<./resources/1_rZ0PqXf-QHyoA0iJCwnTBw.png>)

I found this particularly useful because it ensures consistency across the entire project, regardless of who or what is doing the implementation.

### 2. Specify Command

The `spec` command implements the "Specify" phase of SDD, answering the "what" question.

**What it does:**

- Executes the `create-new-feature` script
- Creates feature branches and initializes specification files
- Generates structured documentation in the `specs/branch-name/` directory

**Generated Files:**

- `specs/branch-name/checklists/requirements.md`: Detailed requirements checklist
- `specs/branch-name/spec.md`: The primary specification document

**Workflow:**

1. Developer initiates a new feature
2. Script creates the appropriate directory structure
3. Templates are populated with project-specific context
4. Specification document is ready for refinement

This is where you define exactly what needs to be built, without getting into implementation details. Here’s what a specification document looks like:

![](<./resources/1_ezbLicINLycZz9IvKJ9iEg.png>)

### 3. Plan Command

The `plan` command implements the "Plan" phase, addressing technical implementation details.

**What it does:**

- Executes `setup-plan` and `output-agent-content` scripts
- Generates comprehensive planning documentation
- Creates GitHub Copilot-specific instructions

**Generated Files:**

- `plan.md`: Overall implementation plan
- `research.md`: Investigation of technical options
- `data-model.md`: Database schemas and data structures
- `contracts.md`: API contracts and interfaces
- `quickstart.md`: Getting started guide
- `copilot-instructions.md`: Specific instructions for GitHub Copilot agent

**Workflow:**

1. Loads spec.md and constitution.md for context
2. Executes Phase 0 (Research)
3. Executes Phase 1 (Design)
4. Runs `update-agent-context` to maintain AI context
5. Completes the planning workflow with all documentation

The plan template goes as follows:

![](<./resources/1_fER-bXTYA6OINld-tXClkw.png>)

And here’s what an actual generated plan.md looks like:

![](<./resources/1_HPDRFHW-qb5p59Dymn1S5w.png>)

I love how this automatically creates comprehensive documentation that guides both human developers and AI agents through the implementation process.

### 4. Tasks Command

The `tasks` command breaks down the plan into actionable, testable increments.

**What it does:**

- Executes `check-prerequisites` script to validate readiness
- Validates that all necessary documentation exists (spec, plan, data model, etc.)
- Generates a task breakdown

**Generated Files:**

- `specs/branch-name/tasks.md`: Detailed task list with tracking

**Task Characteristics:**

- Actionable: Each task can be clearly defined and executed
- Testable: Completion can be verified
- Independent: Tasks can be worked on in parallel where possible
- Phase-based: Organized by development phase
- Time-bounded: Estimates for completion

Here’s what a task breakdown looks like:

![](<./resources/1_CvOS861gZHeth7ILiObWaQ.png>)

This is where the rubber meets the road — breaking down the plan into concrete, actionable steps.

### 5. Implement Command

The `implement` command brings specifications to life by generating actual code.

**What it does:**

- Executes various commands (git operations, code generation, etc.)
- Leverages GitHub Copilot for code generation
- Updates task tracking

**Generated Artifacts:**

- Project source code
- Updated `tasks.md` with completed items marked

**Workflow:**

1. Processes task list sequentially or in parallel
2. Uses GitHub Copilot to generate code based on specifications
3. Executes git operations for version control
4. Updates progress tracking
5. Provides status on completed and remaining work

**Critical Principle**: Implement code step-by-step based on phases or tasks. Avoid generating the entire project all at once.

I learned this the hard way — generating too much code at once makes it difficult to review and verify. Better to work in small increments.

The app finally built based on the SDD workflow looks like this:

![](<./resources/1_j5OL0ZtRTvrQiKPHBAPcGA.png>)

## Practical Implementation Tips

From my experience working with SpecKit, here are some key insights:

1. **Start with Familiar Projects**: Begin with a project you know well — where you understand both the business requirements and code implementation. This allows you to validate SpecKit’s output effectively.
2. **Follow Official Examples**: Track GitHub’s official projects from scratch to understand the SDD approach and SpecKit’s operating principles. This really helped me get up to speed quickly.
3. **Human in the Loop**: Do not place absolute trust in AI. Human intervention and manual verification are necessary at critical steps to gradually build confidence in the tool. This is particularly important when you’re first getting started.

## Summary

Spec Driven Development represents a significant evolution in software development methodology, particularly well-suited to the AI-assisted programming era. GitHub SpecKit provides a practical, implementable framework for applying SDD principles, integrating seamlessly with GitHub Copilot to create a powerful development workflow.

By moving from the informality of vibe coding to the structured approach of SDD, teams can achieve:

- **Higher Quality Code**: Clear specifications lead to better AI-generated code
- **Better Maintainability**: Living documentation evolves with the codebase
- **Improved Collaboration**: Common language for all stakeholders
- **Scalable Process**: Approach works from prototypes to production systems
- **AI Optimization**: Well-structured context enables better AI agent performance

As AI continues to transform software development, methodologies like SDD that provide structure and clarity will become increasingly important. GitHub SpecKit offers a practical path forward, allowing teams to embrace AI-powered development while maintaining the discipline and quality standards essential for successful software projects.

In my next articles, I’ll share more about advanced SDD techniques and how to integrate them with existing development workflows. But for now, I encourage you to try SpecKit with one of your own projects — you might be surprised at how much it transforms your AI-assisted development process.

Happy AI coding!

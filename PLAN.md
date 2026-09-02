You are Spec Driven Development specialist and you are addopting the fundamental 
philosophy  of SDD to AYON project. Read [SDD-instructions.md](./SDD-instructions.md) 
To better understand the philosophy instructions. 

From **My Current DevelopmentWorkflow** section and subsections learn about my 
current development workflow with all the limints.

Output of this plan should be considered only as research and design and see 
**Output** section for the implementation plan. Make sure you meet all criteria 
from **Agentic develomplent requirements** section.

There will be two phases of this project:
- **Research and Design** - output of this phase is described in **Output** section
                            This will be then used as input for **Implementation** phase
- **Implementation** - implementing and developing the SDD workflow for local and 
                       remote development


# Folder Structure

## project folder strucutre (mainly for my own zed IDE ):

``__YNPUT`` - this <root project folder> (the one you are reading)

## Agentic related projects (learn about those and include them in SDD for addon distributed SDD workflows)

``ayon-agentic-instructions`` - Agentic related repository

## client related folders (learn about those and include them in SDD for addon development)

``ayon-core`` - AYON client core folder 
``ayon-launcher`` - AYON client launcher folder

## addon related folders (learn about those and include them in SDD and each needs to get addon related instructions)

``ayon-batch-delivery`` - my project domain AYON client addon folder (include it in SDD)
``ayon-nuke`` - my project domain AYON client addon folder (include it in SDD)
``ayon-flame`` - my project domain AYON client addon folder (include it in SDD)
``ayon-resolve`` - my project domain AYON client addon folder (include it in SDD)
``ayon-hiero`` - my project domain AYON client addon folder (include it in SDD)

## server related folders (do not touch those)

``ayon-docker`` - AYON server docker stack
``ayon-backend`` - AYON server backend folder
``ayon-frontend`` - AYON server frontend folder

# Guardrails

- Do not spend too much tokens on learning each folder. Try to minimize by 
  only reading the basic tree structure of the project folders. And if it is not 
  enough, basic from ``api`` or ``__init__.py`` files or docstrings. 
- Be economical and only read what you need to understand the project based on 
  the Instructions. 
- Do not touch following folders:
  - ``__TESTs`` - my own test folders and data
  - ``.venv`` - my own virtual environment
  - ``.*\.worktrees`` or ``./worktrees`` - agentic related worktrees
  - ``.env`` or ``.env.*`` - my own environment variables
  - ``uv.*`` - my own uv tooling
  - any folder starting with ``ayon-`` which is not in defined in **Folder Structure**
- Any new code and distribution needs to be ideally excluded from repository 
  code as much as possible. But If it would not be possible then it can be added to the repository.
- Some basic SDD development had been already done in ``ayon-agentic-instructions`` and can be used
  as main repository for general SDD development for AYON project.
- Addon related SDD development should be done in each addon repository folder 
  but at minimum required.
- **zed** development related files and config should ideally be excluded from each repository and 
  managed perhaps to be only included dynamically by some ZED available scripting and tooling with 
  available callbecks or hooks. So for example if I Open the repository for an addon folder
  some hook will automatically include the <root project folder>/.zed folder. And rewire necessary all paths
  to use the <root project folder>/.zed or its linked ``<root project folder>/src`` folder as the root 
  zed tasks are referencing it from ``<root project folder>/project.toml``.

# My Current DevelopmentWorkflow
## Learn about the Project
The <root project folder> is containing folders for a multirepository project learn 
about them in **Folder Structure** and follow **Guardrails** section for more details.

## Learn about my personal development
The <root project folder> is a personal wrapper and it is not officially part of the project. 
It is my personal development project where I mainly use ``.zed`` folder for tasks 
and other tooling those could be found in ``src``. 
But during the Zed development I tend to jump into individual folders, 
for example into ``ayon-batch-delivery`` or ``ayon-nuke`` so my agentic workflow 
does not get confused with other folders in the ``__YNPUT`` folder. 
Usually I am creating ``worktrees`` for each individual folder so I can work 
on agentic tasks separately. 

## What are mine limitations
- Once I am jumping into individual AYON folder I am loosing zed tasks and context
- once I am working on a worktree an agent does not have access to SDD 
  instrucitons which are not part of repository

## What I am using for Agentic development
- usually Zed for agentic development but also GitHub Copilot on local or  
  at Github agentic acions. Currently I am using **goose acp** in Zed 
  or **goose desktop** or **goose cli**. 


# Instructions
- dynamic distribution of zed related config to addon folders or its related worktrees
- addon related SDD instructions where some of them could be part of the repository
- generic AYON related SDD instructions kept in ``ayon-agentic-instructions`` repository
  but somehow distributed to all addon folders. See some related development in 
  ``ayon-nuke`` repository where I tried to design the worklfow with softlinking 
  and ``.githooks`` for worktree distribution. This might not be the ideal approach
  but it could be a good starting point. If you figure out during your reseach with all 
  the requirements you need to meet suggest it in ``IMPLEMENTATION-PLAN.md``.


# Agentic develomplent requirements
- all created SDD instructions should be usable universally by all available agentic workflows. 
- This SDD will be used locally at my workstation and at Github or Kilo or 
  Claude or Goose agentic actions.
- This project will be processed by **goose** agentic workflow. If you figure out you will need to create
  some tooling for the IMPLEMENTATION phase then suggest them.
- For local development 
  - I am able to use local inference for some smaller tasks and perhaps some 
    goose/zed/copilot/kilo subagents/recipes could specifically tackle some of those tasks, suggest them. 
  - It might be helpfull to use local inference for vectorisation embedding 
    generation and goose/zed/copilot/kilo subagents/recipes might be able to tackle it, suggest it.

# Output
- All your research shoud be added to ``<root project folder>/IMPLEMENTATION-PLAN.md``. 
  This file should be agentic instructions for **goose** agentic workflow to 
  implement in next phase.
- This phase is not developing and implementing anything, its only output is the 
  ``IMPLEMENTATION-PLAN.md`` file with agentic instructions for **goose** agentic workflow.

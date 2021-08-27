.PHONY: build package changes deploy-core deploy-pipelines deploy destroy-core destroy-pipelines destroy

# define the name of the virtual environment directory
VENV := .venv
VENV_ACTIVATE := .venv/bin/activate

# default target, when make is executed without arguments: install virtualenv and project dependencies 
all: install

# Create virtualenv and install dependencies
install:
	@( \
		python3 -m venv $(VENV); \
		source $(VENV_ACTIVATE); \
		pip install -r requirements.txt; \
	  \
	)

# Bootstraping the cdk
bootstrap:
ifeq ("$(account-id)","")
	@echo "Error: account-id parameter is mandatory\n"
	@exit 1
endif
ifeq ("$(region)","")
	@echo "Error: region parameter is mandatory\n"
	@exit 1
endif
	@( \
		source $(VENV_ACTIVATE); \
		cdk bootstrap aws://${account-id}/${region}; \
	  \
	)

# Deploy monorepo core stack
deploy-core :
ifneq ("$(monorepo-name)","")
	$(eval params_monorepo := --parameters MonorepoName=$(monorepo-name))
endif
	@( \
		source $(VENV_ACTIVATE); \
		echo cdk deploy MonoRepoStack ${params_monorepo}; \
		cdk deploy MonoRepoStack ${params_monorepo}; \
	  \
	)

# Deploy pipelines stack
deploy-pipelines:
	@( \
		source $(VENV_ACTIVATE); \
		cdk deploy PipelinesStack; \
	   \
	)

# Deploy both stacks
deploy: deploy-core deploy-pipelines

# Destroy MonoRepo core stack
destroy-core:
	@( \
		source $(VENV_ACTIVATE); \
		cdk destroy MonoRepoStack; \
	   \
	)

# Destroy Pipelines stack
destroy-pipelines:
	@( \
		source $(VENV_ACTIVATE); \
		cdk destroy PipelinesStack; \
	   \
	)

# Remove virtual env files
clean-files:
	rm -rf $(VENV)
	find . -type f -name '*.pyc' -delete

# Destroy all
destroy: destroy-pipelines destroy-core clean-files
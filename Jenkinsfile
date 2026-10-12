pipeline {
    agent any

    environment {
        IMAGE_NAME = 'aceest-fitness'
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    triggers {
        // Poll GitHub every 5 minutes (use a GitHub webhook instead if Jenkins is publicly reachable)
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
            }
        }

        stage('Setup Python Env') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements-dev.txt
                '''
            }
        }

        stage('Build & Lint') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python -m py_compile app.py db.py fitness.py
                    flake8 .
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python -m pytest --junitxml=test-results.xml --cov=. --cov-report=term
                '''
            }
            post {
                always { junit 'test-results.xml' }
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build --target runtime -t $IMAGE_NAME:$IMAGE_TAG -t $IMAGE_NAME:latest .'
            }
        }

        stage('Test in Container') {
            steps {
                sh '''
                    docker build --target test -t $IMAGE_NAME-test:$IMAGE_TAG .
                    docker run --rm $IMAGE_NAME-test:$IMAGE_TAG
                '''
            }
        }
    }

    post {
        success { echo "BUILD #${env.BUILD_NUMBER} passed the quality gate." }
        failure { echo "BUILD #${env.BUILD_NUMBER} FAILED - check the stage logs above." }
        always  { sh 'docker image prune -f || true' }
    }
}

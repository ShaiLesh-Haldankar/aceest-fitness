pipeline {
    agent any

    environment {
        IMAGE      = 'sh00010111/aceest-fitness'
        SONAR_HOST = 'http://localhost:9000'
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '15'))
    }

    triggers {
        // Poll GitHub every 2 minutes and build automatically on new commits
        pollSCM('H/2 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
                script {
                    env.APP_VERSION = sh(script: '''sed -n 's/^APP_VERSION = "\\(.*\\)"/\\1/p' app.py''', returnStdout: true).trim()
                    env.GIT_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
                echo "Building ACEest Fitness version ${env.APP_VERSION} (commit ${env.GIT_SHORT})"
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
                    python -m pytest --junitxml=test-results.xml --cov=. --cov-report=xml --cov-report=term
                '''
            }
            post {
                always { junit 'test-results.xml' }
            }
        }

        stage('SonarQube Analysis & Quality Gate') {
            steps {
                withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                    sh '''
                        docker run --rm --network host -u "$(id -u):$(id -g)" \
                          -e SONAR_HOST_URL="$SONAR_HOST" -e SONAR_TOKEN="$SONAR_TOKEN" \
                          -v "$PWD:/usr/src:z" sonarsource/sonar-scanner-cli:5.0.1 \
                          -Dsonar.projectVersion="$APP_VERSION"
                        bash scripts/sonar_gate.sh
                    '''
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build --target runtime -t $IMAGE:$APP_VERSION -t $IMAGE:build-$BUILD_NUMBER .
                    docker build --target test -t aceest-fitness-test:$BUILD_NUMBER .
                '''
            }
        }

        stage('Test in Container') {
            steps {
                sh 'docker run --rm aceest-fitness-test:$BUILD_NUMBER'
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
                    sh '''
                        echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                        docker push $IMAGE:$APP_VERSION
                        docker push $IMAGE:build-$BUILD_NUMBER
                        docker tag $IMAGE:$APP_VERSION $IMAGE:latest
                        docker push $IMAGE:latest
                        docker logout
                    '''
                }
            }
        }

        stage('Archive Build Artifacts') {
            steps {
                sh '''
                    git archive --format=tar.gz -o aceest-fitness-$APP_VERSION.tar.gz HEAD
                    printf "version=%s\\ncommit=%s\\nbuild=%s\\nimage=%s:%s\\n" "$APP_VERSION" "$GIT_SHORT" "$BUILD_NUMBER" "$IMAGE" "$APP_VERSION" > build-info.txt
                '''
                archiveArtifacts artifacts: 'aceest-fitness-*.tar.gz, build-info.txt, test-results.xml, coverage.xml, sonar-report.txt',
                                 fingerprint: true, allowEmptyArchive: true
            }
        }
    }

    post {
        success { echo "BUILD #${env.BUILD_NUMBER} (v${env.APP_VERSION}) passed all stages and was pushed to Docker Hub." }
        failure { echo "BUILD #${env.BUILD_NUMBER} FAILED - see the failing stage log." }
        always  { sh 'docker image prune -f || true' }
    }
}

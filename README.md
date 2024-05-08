# Upload Manager

Upload Manager is a versatile microservice designed to monitor specified directories that are shared in Docker volumes, manage uploads to AWS S3, and facilitate data purging. It integrates seamlessly with various modules, providing robust logging and AWS credential configuration features.

## Features

- **Directory Monitoring:** Continuously monitors any listed directory shared in Docker volumes.
- **Backup to S3:** Enables users to back up important data to AWS S3 seamlessly.
- **Data Purging:** Automates the purging of old or unnecessary data to manage storage efficiently.
- **S3 Object Listing and Downloading:** Allows users to list all uploaded objects to S3 and facilitates easy downloading.
- **AWS Credential Configuration:** Supports configuration of AWS credentials to securely access AWS services.
- **Integration and Logging:** Designed as a microservice, it easily integrates with other modules and provides comprehensive logging capabilities.

## Tools Used

- Flask
- Boto3
- Threading
- Docker
- SQLAlchemy

## Limitation

- The current version of Upload Manager is only compatible with Linux-based operating systems.

## Getting Started

### Prerequisites

Ensure you have Docker and Python installed on your Linux system. The project is built using Python 3.8 or later.

### Installation

#### 1. Clone the repository:

   ```bash
   git clone https://github.com/yourgithubusername/upload-manager.git
   cd upload-manager
   ```

#### 2. Configure Environment Variables
Before building the Docker images, you may need to adjust the environment variables used by the application. These variables are set in the docker-compose.yml file. Edit this file to change any values as required:


#### 3. Build the Docker Containers
Run the following command to build the Docker containers. This will fetch the base images, install dependencies, and prepare your application's Docker environment:

   ```bash
   docker-compose build
   ```

#### 4. Start the Application
Start the application in detached mode using Docker Compose:

   ```bash
   docker-compose up -d
   ```
This command will start the containers in the background. To view logs, use docker-compose logs -f.

#### 5: Access the Application
Once the containers are running, open your web browser and navigate to:

   ```bash
   http://127.0.0.1:5000/
   ```
This URL will direct you to the home page of the Employee Management System where you can interact with the application.

#### Stopping the Application
To stop the running containers:


   ```bash
   docker-compose down
   ```


## License

- Distributed under the MIT License. See LICENSE for more information.

## Contact

- Shahsank Marwade– shashankmarwade99@gmail.com

- Project Link: https://github.com/Shashank-Marwade/upload-manager

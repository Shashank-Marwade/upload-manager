FROM python:3.9

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file to the container
COPY requirements.txt /usr/src/app/

# RUN pip install -q -U --prefer-binary --no-cache-dir -r requirements.txt
# Install the app dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code to the container
COPY . /usr/src/app/

# Set the command to run your app
CMD ["python3", "uploader.py"]

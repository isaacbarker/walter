FROM python:3-alpine3.22

WORKDIR /walter

# Install dependencies and Gunicorn
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt \
    && pip3 install --no-cache-dir gunicorn

# Copy app source
COPY . .

# Expose the port your app will run on
EXPOSE 5500

# Run with Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5500", "main:app"]
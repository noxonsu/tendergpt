FROM python:3.10-slim-bullseye

RUN apt-get update && \
apt-get install -yq gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 \
libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 \
libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 \
fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf \
ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget && \
wget https://github.com/Yelp/dumb-init/releases/download/v1.2.1/dumb-init_1.2.1_amd64.deb && \
dpkg -i dumb-init_*.deb && rm -f dumb-init_*.deb && \
apt-get clean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -yq xvfb x11vnc x11-xkb-utils xfonts-100dpi xfonts-75dpi xfonts-scalable xfonts-cyrillic x11-apps

# Install Python dependencies
COPY requirements.txt /app/
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Note: If you're using Puppeteer-Py, you can include it in the requirements.txt

# Setup user for running the application
RUN groupadd -r pptruser && useradd -r -g pptruser -G audio,video pptruser && \
    chown -R pptruser:pptruser /app

# Set language to UTF8
ENV LANG="C.UTF-8"

# Use the non-root user to run our application
USER pptruser

# --cap-add=SYS_ADMIN
# https://docs.docker.com/engine/reference/run/#additional-groups

ENTRYPOINT ["dumb-init", "--"]

# Creating Display
ENV DISPLAY :99

# Start script on Xvfb
CMD Xvfb :99 -screen 0 1024x768x16 & python getTenderFiles2.py

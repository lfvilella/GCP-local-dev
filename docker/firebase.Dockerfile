FROM google/cloud-sdk:338.0.0

RUN apt-get update && apt-get install -y curl sudo

RUN curl -sL firebase.tools | bash


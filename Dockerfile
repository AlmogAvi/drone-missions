FROM px4io/px4-dev-simulation-jammy:latest

# התקנת כלים לבניית rvo2
RUN apt-get update && apt-get install -y python3-dev python3-setuptools \
    build-essential cmake git && rm -rf /var/lib/apt/lists/*

# התקנת ספריות פייתון
RUN pip3 install --upgrade pip cython && \
    pip3 install mavsdk pandas numpy matplotlib && \
    pip3 install git+https://github.com/snape/RVO2

WORKDIR /workspace
COPY . /workspace

CMD ["bash", "-lc", "cd /PX4-Autopilot && make px4_sitl_default jmavsim"]

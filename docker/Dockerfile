FROM python:3.6
ENV TZ=Europe/Kiev
RUN mkdir app
STOPSIGNAL SIGINT

#-------------------- Python requirements----
WORKDIR /
ADD build_requirements.txt /build_requirements.txt
RUN pip install -r build_requirements.txt
RUN rm build_requirements.txt
WORKDIR app/

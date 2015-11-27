FROM debian
ENV DEBIAN_FRONTEND=noninteractive LIBNAME=thinserve
RUN apt-get -y update && apt-get -y install python python-pip python-dev
RUN pip install 'mock == 1.0.1'
RUN pip install 'twisted == 15.2.1'
RUN pip install 'functable == 0.2.dev1'
COPY . $LIBNAME
WORKDIR $LIBNAME
RUN pip install .
CMD trial $LIBNAME

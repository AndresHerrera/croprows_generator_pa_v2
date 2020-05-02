FROM python:2.7
RUN python -m pip install --upgrade pip
RUN mkdir /app
COPY requirements.txt /app
COPY croprows-api /app/croprows-api
COPY croprows-cli /app/croprows-cli
RUN chmod +x /app/croprows-cli/crg_cli.sh
RUN mkdir -p /app/orthomosaics
RUN chmod -R 0777 /app/orthomosaics
RUN pip install --requirement /app/requirements.txt
VOLUME /app/orthomosaics
WORKDIR /app
ENTRYPOINT ["python"]
CMD ["croprows-api/croprows-api.py"]

# Google Cloud Platform Local Development 

This demo project demonstrating how to work GCP products using Python in dev env offline without need of internet.

## You will find examples of using:

- [Datastore](https://cloud.google.com/datastore)
- [Cloud Storage](https://cloud.google.com/storage)
- [Firestore](https://cloud.google.com/firestore)
- [Cloud Tasks](https://cloud.google.com/tasks)
- [Cloud Scheduler](https://cloud.google.com/scheduler)

## The project

This is a very basic project where the `POST /item` creates an Item in the Datastore, then schedule backgroud Cloud Tasks to update Firestore and generate a CSV that is uploaded to Cloud Storage.

The project structure consists in:

- [main.py](backend/main.py) where the HTTP handlers for the endpoints are located
- [services.py](backend/services.py) for the business rules
- [gcp_utils](backend/gcp_utils/) a package with helper methods related to Google Cloud Patform products

## Running the project locally

At the first time running the project run the command:

    $ make build

Then you can start and stop the local dev running:

    $ make up
    $ make down

Run `make help` in order to get the available commands

    $ make help

Once the project is running check out http://localhost:8080/docs and play with the avaliable APIs.

![create_item](https://user-images.githubusercontent.com/45940140/118045846-db1f1380-b34e-11eb-9dc4-ef8a9ec39f5b.gif)

## Deploying to GCP

    $ make gcp-connect
    $ make gcp-deploy
    $ gcp-browse

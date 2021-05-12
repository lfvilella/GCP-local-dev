# Google Cloud Platform Local Development 

This project demonstrates how to work GCP products on dev env all offline without need to internet.

## You will find examples of using:

- [Datastore](https://cloud.google.com/datastore)
- [Cloud Storage](https://cloud.google.com/storage)
- [Firestore](https://cloud.google.com/firestore)
- [Cloud Tasks](https://cloud.google.com/tasks)
- [Cloud Scheduler](https://cloud.google.com/scheduler)

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

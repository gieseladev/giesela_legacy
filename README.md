# Giesela Refresh

[![CircleCI](https://circleci.com/gh/gieseladev/giesela.svg?style=svg)](https://circleci.com/gh/gieseladev/giesela)
[![License](https://img.shields.io/github/license/gieseladev/giesela.svg?branch=refresh)](https://github.com/GieselaDev/Giesela/blob/refresh/LICENSE)

Meet the next version of Giesela! I guess it's no longer the "next" version
but the current one... Let's just keep saying "next" because it sounds
cooler.


## What is Refresh?
This is the `refresh` version of Giesela. What does that mean exactly? Who knows...
Anyway, this is a stripped-down, containerised version of Giesela. It's
containerised which - as we all know - improves everything by about 1000%...


## Running
Instead of making things hard, why don't we just ignore manual setup and go straight
to something as easy as running a [Docker Container](https://www.docker.com/resources/what-container).

Get the official image from `giesela/giesela:refresh` and just run it!
Even better, if you just want it to run without having to do all that much
you can use the [docker-compose](https://www.linode.com/docs/applications/containers/how-to-use-docker-compose/)
file which comes with the necessary services.
(You still have to do some configuration though,
refer to the next section for details)


## Configuration
Please look at the `config.yml` file in the `data` directory for
instructions on how to configure Giesela.


### Volumes (Docker)
You can mount `/giesela/data` which holds a lot of Giesela's static data
(certificates, lyrics, options, and so on).

> Keep in mind that these files will be overwritten with newer versions if there are any.
> Currently this only affects `radio_stations.yml`

`/giesela/logs` holds the log files (if there even are any...)


### Secure WebSockets for Webiesela
Giesela refresh supports SSL encryption for Webiesela. All you have to do
to enable it is place your certificate file in the `data/cert` folder.

If you have a separate file for the private key you also need to place it in the same
folder and make sure Giesela can identify which is which. You can do this by either
naming the files `CERTIFICATE` vs `PRIVATEKEY` / `KEYFILE` or you can just give them
the suffix `.cert` vs `.key`.
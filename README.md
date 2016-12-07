Caroline 
====
Version 1.0


##### What is Caroline?
Caroline is a wrapper that facilitates job submission to Torque for Docker containers!

##### How does it work?
Caroline creates performs a 3 step process to make magic happen:

1. A wrapper for `cli.mk_pilot` is created for a specific job that specifies 4 things
    1. A data volume to mount to the Docker container. (e.x. `/data`)
    2. A name space (if any) to use in the volume. (e.x. `docker_user`)
    3. A command to run inside the container. 
        (the use of `&&` is the current implimentation to run more than one command)
    4. An image to use for the container! (e.x. `wghilliard/lariatsoft_caroline:1.0`)
2. Caroline submits the task to a Mongo daemon under the database name `caroline`.
3. Caroline creates an executable file in `/tmp` which is run by Torque.

That's it!

##### How do I write a wrapper?
A wrapper's only requirement is to use `mk_pilot`, the rest is handled for you!
A few wrappers have already been created!
- lariatsoft_one - a wrapper that copies in fickle files to perform all three stages of the lariatsoft generation process.
- lariatsoft_two - a wrapper that copies in fickle files and performs the Wire_Dump conversion and H5 conversion on existing `.root` files

##### How do I use a wrapper?
The only "extra" information needed is to properly configure the `config.json` file to store the namespace, image, and data_volume parameters.

NOTE: a connection to the Mongo database is required!!

    from mongoengine import connect
    connect("caroline")

##### Example:

    from caroline.wrappers import lariatsoft_two
    lariatsoft_two("/Users/wghilliard/single_gen_2.root", "/data/docker_user/fcl_files/WireDump_3D.fcl",
                   "/data/docker_user/grayson_test_2")
                   
##### Extra
- All container logs are stored in `$DATA_VOLUME/$NAMESPACE/logs/$C_ID`
- This is version 1.0 so there might be bugs! Please open github issues if you find any!
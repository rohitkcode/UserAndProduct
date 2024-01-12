# UserAndProduct
 RESTful service for a product catalog with basic user authentication.

 1. Clone the repository to the local.
 2. Use docker-compose.yml to run the app:
    run: sudo docker-compose up -d
 3. The app will start running on "http://localhost:8080/".
 4. Access "http://localhost:8080/docs" for Swagger UI to test the api calls.
 5. APIs supported for user access and authentication
    * /register
    * /login
    * /logout
    * /delete
 6. APIs supported for user specific product portfolio:
    * /add_product
    * /list_products
    * /product_details
    * /remove_product

Note:
* For user authentication only hash of the password is getting stored for safety and session verification is also done.
* The app is developed in Python using FASTapi.
* SQLite is being used for storing user data.
* MongoDB is being used to store product informations.

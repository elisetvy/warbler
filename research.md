1. How is the logged in user being kept track of?
By the add_user_to_g function.

2. What is Flask’s g object?
It is a special global object that allows us to store data that is specific to a single request which makes it accessible throughout the duration of that request which in turn allows us to share data between functions. You can treat it like a dictionary. You can select a key and value. G is not appropriate for storing data across requests.

3. What is the purpose of add_user_to_g?
To see if there is logged in user, and if so, to make that user more easily accessible.

4. What does @app.before_request mean?
It executes the function before every request.
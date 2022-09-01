upload_block = """
        <div style="background-color: #707bb2; margin: 15px; border-radius: 5px; padding: 15px; width: 300px">
        <b>Add to your video library: </b>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <p><input type=file name=file value="Pick a Movie">
            <p><input type=submit value="Upload">
        </form>
        </div>"""
sign_up_login_block = """
        <div style="background-color: #707bb2; margin: 15px; border-radius: 5px; padding: 15px; width: 180px">
        <b>Sign Up:</b>
        <form action="/sign-up" method="post">
            <p><input type=text name=email>
            <p><input type=text name=password>
            <p><input type=submit value="Sign-up">
        </form>
        <b>Login:</b>
        <form action="/login" method="post">
            <p><input type=text name=email>
            <p><input type=text name=password>
            <p><input type=submit value="Login">
        </form>
        </div>
        """
logout_block = """
        <form action="/logout" method="get">
            <p><input type=submit value="Logout">
        </form>"""
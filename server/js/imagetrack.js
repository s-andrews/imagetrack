const backend = "/cgi-bin/imagetrack_server.py"
var session = ""
var configuration = ""
var selected_project_oid = ""

$( document ).ready(function() {
    show_login()

    // Action when they log in
    $("#login").click(process_login)
    $("#password").keypress(function(e){
        if(e.keyCode == 13){
            process_login();
        }
    });

    // Action when they log out
    $("#logout").click(logout)

    // Action for starting a new project
    $("#newproject").click(new_project)

    // Action for submitting a new project
    $("#create_project").click(create_project)

    // Action when clicking on a project
    $('#projecttable tbody').on('click', 'tr', select_project)

    // Make tag name suggestions
    $("#projecttagname").keyup(suggest_tags);

    // Action when adding a new project tag
    $("#addprojecttag").click(add_project_tag)

    // Action when adding a new project comment
    $("#addprojectcomment").click(add_project_comment)

    // Make the extensions table a Data Table
    $("#extensions").DataTable({paging: false, autoWidth: false, searching: false, info: false})

    // Make the main project list a Data Table
    $('#projecttable').DataTable({lengthChange: false, pageLength: 5});

    // Make the file tree a jstree
    $("#filetree").jstree({'core': {'data':[]}})

})


function show_login() {

    // Check to see if there's a valid session ID we can use

    session = Cookies.get("imagetrack_session_id")
    if (session) {
        // Validate the ID
        $.ajax(
            {
                url: backend,
                method: "POST",
                data: {
                    action: "validate_session",
                    session: session,
                },
                success: function(session_string) {
                    if (!session_string.startsWith("Success:")) {
                        session = ""
                        Cookies.remove("imagetrack_session_id")
                        $("#logindiv").modal("show")
                        show_login()
                        return
                    }
                    var realname = session_string.substring(9)
                    $("#logindiv").modal("hide")

                    load_initial_content()

                },
                error: function(message) {
                    console.log("Existing session didn't validate")
                    $("#logindiv").modal("show")
                }
            }
        )
    }
    else {
        $("#logindiv").modal("show")
    }
}

function logout() {
    session_id = ""
    Cookies.remove("imagetrack_session_id")
    $("#maincontent").hide()
    $('#projecttable').DataTable().rows().remove()

    $("#selectedprojectname").text("")
    $("#selectedprojectfolder").text("")    

    $("#projecttags").empty()
    $("#projectcomments").empty()

    $("#logindiv").modal("show")
}




function process_login() {
    let email = $("#email").val()
    let password = $("#password").val()

    // Clear the password so they can't do it again
    $("#password").val("")

    $.ajax(
        {
            url: backend,
            method: "POST",
            data: {
                action: "login",
                email: email,
                password: password
            },
            success: function(session_string) {
                let sections = session_string.split(" ")
                if (!session_string.startsWith("Success")) {
                    $("#loginerror").html("Login Failed")
                    $("#loginerror").show()
                    return
                }
                $("#loginerror").hide()
                session = sections[1]

                Cookies.set("imagetrack_session_id", session, { secure: false })
                show_login()
            },
            error: function(message) {
                $("#loginerror").html("Login Failed")
                $("#loginerror").show()
            }
        }
    )
}


const backend = "/cgi-bin/imagetrack_server.py"
var session = ""
var configuration = ""

$( document ).ready(function() {
    show_login()

    // Action when they log in
    $("#login").click(process_login)

    // Action when they log out
    $("#logout").click(logout)

    // Action for a new project
    $("#newproject").click(new_project)


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
                    $("#maincontent").show()
    
                    // Get their list of projects
                    update_projects()
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
    $('#projecttable').DataTable().clear()
    $("#logindiv").modal("show")
}


function new_project() {

    // Load the configuration if it's not here already
    if (!configuration) {
        $.ajax(
            {
                url: backend,
                method: "POST",
                data: {
                    action: "configuration"
                },
                success: function(configuration_data) {
                    configuration = configuration_data
                    console.log(configuration)

                    // Update the new project form
                    let s = $("#project_instrument")
                    s.empty()
                    for (let i in configuration.instruments) {
                        s.append(`<option>${configuration.instruments[i]}</option>`)
                    }

                    s = $("#project_modality")
                    s.empty()
                    for (let i in configuration.modalities) {
                        s.append(`<option>${configuration.modalities[i]}</option>`)
                    }

                    s = $("#project_organism")
                    s.empty()
                    for (let i in configuration.organisms) {
                        s.append(`<option>${configuration.organisms[i]}</option>`)
                    }




                },
                error: function(message) {
                    console.log("Failed to retrieve configuration")
                }
            }
        )
    }


    $("#newprojectdiv").modal("show")
}

function process_login() {
    email = $("#email").val()
    password = $("#password").val()

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

                Cookies.set("imagetrack_session_id", session)
                show_login()
            },
            error: function(message) {
                $("#loginerror").html("Login Failed")
                $("#loginerror").show()
            }
        }
    )
}

function update_projects(){

    $.ajax(
        {
            url: backend,
            method: "POST",
            data: {
                action: "list_projects",
                session: session
            },
            success: function(projects) {
                $("#projectbody").empty()

                let t = $('#projecttable').DataTable();

                for (let p in projects) {
                    let project = projects[p]
                    t.row.add([
                        project["name"],
                        project["date"],
                        project["instrument"],
                        project["modality"],
                        "Folder"
                    ]).draw(false)
                }


            },
            error: function(message) {
                $("#projectbody").clear()
            }
        }
    )

}
const backend = "/cgi-bin/imagetrack_server.py"
var session = ""
var configuration = ""

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


})

function suggest_tags() {
    let text = $("#projecttagname").val().toLowerCase()

    $("#tagsuggestions").empty()

    for (let i in configuration["tags"]) {
        if (text.length == 0 || configuration["tags"][i].toLowerCase().includes(text)) {
            $("#tagsuggestions").append(`<li><a class="tagsuggestion dropdown-item" href="#">${configuration["tags"][i]}</a></li>`)
        }
    }

    $(".tagsuggestion").unbind()
    $(".tagsuggestion").click(function(e) {
        $("#projecttagname").val($(this).text())
        return(false)
    })
}


function add_project_tag() {
    let folder = $("#selectedprojectfolder").text()
    let tag_name = $("#projecttagname").val()
    let tag_value = $("#projecttagvalue").val()

    $.ajax(
        {
            url: backend,
            method: "POST",
            data: {
                action: "add_tag",
                session: session,
                folder: folder,
                tag_name: tag_name,
                tag_value: tag_value
            },
            success: function(project_json) {
                $("#projecttagname").val("")
                $("#projecttagvalue").val("")
                update_selected_project(folder)
            },
            error: function(message) {
                console.log("Failed to add tag")
            }
        }
    )
}

function add_project_comment() {
    let folder = $("#selectedprojectfolder").text()
    let comment_text = $("#projectcommenttext").val()

    $.ajax(
        {
            url: backend,
            method: "POST",
            data: {
                action: "add_comment",
                session: session,
                folder: folder,
                comment_text: comment_text
            },
            success: function(project_json) {
                $("#projectcommenttext").val("")
                update_selected_project(folder)
            },
            error: function(message) {
                console.log("Failed to add comment")
            }
        }
    )
}


function select_project() {
    let table = $('#projecttable').DataTable();
    let data = table.row( this ).data();

    // We use the folder as the unique key to get the project
    // details from the back end.  We'll get the full details
    // and show them in a div below.
    let folder = data[5]

    $("#selectedprojectname").text(data[0])
    $("#selectedprojectfolder").text(folder)    
    update_selected_project(folder)
}

function update_selected_project (folder) {

    $.ajax(
        {
            url: backend,
            method: "POST",
            data: {
                action: "project_details",
                session: session,
                folder: folder
            },
            success: function(project_json) {

                let t = $("#projecttags")
                t.empty()

                for (let i in project_json["tags"]) {
                    t.append(`
                    <div class="row">
                    <div class="col-md-1"></div>
                    <div class="col-md-3 tagname">${i}</div>
                    <div class="col-md-4 tagvalue">${project_json["tags"][i]}</div>
                    </div>
                    `)
                }

                let c = $("#projectcomments")
                c.empty()
                for (let i in project_json["comments"]) {
                    c.append(`
                    <div class="row">
                    <div class="col-md-1"></div>
                    <div class="col-md-11 commentdate">${project_json["comments"][i]["date"]}</div>
                    </div>
                    <div class="row">
                    <div class="col-md-1"></div>
                    <div class="col-md-11 commenttext">${project_json["comments"][i]["text"]}</div>
                    </div>
                    `)
                }

                $("#projectdetails").show()
            },
            error: function(message) {
                console.log("Couldn't get details for project")
                $("#projectdetails").hide()
            }
        }
    )

}


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

                    // Load the config
                    load_configuration()

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

function load_configuration () {
    // Loads the main config and populates the appropriate fields.

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

                    // Run the function to update tag suggestions to populate the list
                    suggest_tags()


                },
                error: function(message) {
                    console.log("Failed to retrieve configuration")
                }
            }
        )
    }

}


function new_project() {

    $("#newprojectdiv").modal("show")
}


function create_project () {

    // Collect the information we need
    // TODO: Do something sensible if they haven't given everything
    let project_name = $("#project_name").val()
    let project_instrument = $("#project_instrument").val()
    // The modality is actually an array since they can select multiple values
    let project_modality = $("#project_modality").val()
    let project_organism = $("#project_organism").val()

    $.ajax(
        {
            url: backend,
            method: "POST",
            data: {
                action: "new_project",
                session: session,
                name: project_name,
                instrument: project_instrument,
                modality: project_modality,
                organism: project_organism
            },
            success: function(new_project_details) {

                // Add this to the list of projects and show its details
                // Not the most elegant way to do this
                // TODO: Be more elegant!
                update_projects()


                // Remove the new project dialog
                $("#newprojectdiv").modal("hide")

            },
            error: function(message) {
                console.log("Failed to create project")
            }
        }
    )
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
                t.clear()

                for (let p in projects) {
                    let project = projects[p]
                    let i = t.row.add([
                        project["name"],
                        project["date"],
                        project["instrument"],
                        project["modality"].join(", "),
                        project["organism"],
                        project["folder"]
                    ]).index();

                    // Now we can add the project oid to the tr as a 
                    // data attribute so we can find the project oid
                    // easily when someone clicks on it.
                    console.log(t.rows(i).nodes().to$())
                    t.rows(i).nodes().to$().attr("data-oid",project["_id"]["$oid"])

                }

                t.draw();
            },
            error: function(message) {
                $("#projectbody").clear()
            }
        }
    )

}
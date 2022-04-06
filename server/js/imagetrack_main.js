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
    let tag_name = $("#projecttagname").val()
    let tag_value = $("#projecttagvalue").val()

    $.ajax(
        {
            url: backend,
            method: "POST",
            data: {
                action: "add_tag",
                session: session,
                oid: selected_project_oid,
                tag_name: tag_name,
                tag_value: tag_value
            },
            success: function(project_json) {
                $("#projecttagname").val("")
                $("#projecttagvalue").val("")
                update_selected_project(selected_project_oid)
            },
            error: function(message) {
                console.log("Failed to add tag")
            }
        }
    )
}

function add_project_comment() {
    let comment_text = $("#projectcommenttext").val()

    $.ajax(
        {
            url: backend,
            method: "POST",
            data: {
                action: "add_comment",
                session: session,
                oid: selected_project_oid,
                comment_text: comment_text
            },
            success: function(project_json) {
                $("#projectcommenttext").val("")
                update_selected_project(selected_project_oid)
            },
            error: function(message) {
                console.log("Failed to add comment")
            }
        }
    )
}


function select_project() {

    // We just grab the oid from the table.
    let table = $('#projecttable').DataTable();

    // Clear out old information

    $("#projectdetails").hide()
    $("#projectloading").show()

    $("#selectedprojectname").text("")
    $("#selectedprojectfolder").text("")    

    let t = $("#projecttags")
    t.empty()

    let c = $("#projectcomments")
    c.empty()

    // We pull the project oid out of the row's data
    // attribute
    let oid = $(this).data("oid")

    update_selected_project(oid)
}

function update_selected_project (project_oid) {

    selected_project_oid = project_oid

    $.ajax(
        {
            url: backend,
            method: "POST",
            data: {
                action: "project_details",
                session: session,
                oid: project_oid
            },
            success: function(project_json) {

                $("#selectedprojectname").text(project_json["name"])
                $("#selectedprojectfolder").text(project_json["folder"])    

                // Create the file tree so they can see the files in there
                let filetree = $("#filetree")
                // Set the new data
                filetree.jstree(true).settings.core.data = [project_json["files"]]
                // Collapse the tree
                filetree.jstree("close_all",-1)
                // Redraw
                filetree.jstree(true).refresh()

                // Create the table of extensions
                let et = $("#extensions").DataTable()

                et.rows().remove()

                for (let i in project_json["extensions"]) {
                    et.row.add([i,project_json["extensions"][i]["files"],project_json["extensions"][i]["size"],readable_size(project_json["extensions"][i]["size"])])
                }

                et.order([2,"desc"])
                et.draw()

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

                $("#projectloading").hide()
                $("#projectdetails").show()
            },
            error: function(message) {
                console.log("Couldn't get details for project")
                $("#projectdetails").hide()
            }
        }
    )

}

function readable_size(bytes) {
    if (bytes > 1024**4) {
        return (bytes/(1024**4)).toFixed(1)+" TB"
    }
    if (bytes > 1024**3) {
        return (bytes/(1024**3)).toFixed(1)+" GB"
    }
    if (bytes > 1024**2) {
        return (bytes/(1024**2)).toFixed(1)+" MB"
    }
    if (bytes > 1024) {
        return (bytes/1024).toFixed(1)+" kB"
    }
        return bytes+" B"

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
                let t = $('#projecttable').DataTable();
                add_project_row(t,new_project_details)

                // Sort the table with newest projects on top
                t.order(1,"desc")
                // Redraw the table
                t.draw()

                // Remove the new project dialog
                $("#newprojectdiv").modal("hide")

                // Select the newly added project
                console.log(new_project_details)
                update_selected_project(new_project_details["_id"]["$oid"])


            },
            error: function(message) {
                console.log("Failed to create project")
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
                    add_project_row(t,project)
                }

                t.order(1,"desc")
                t.draw()
            },
            error: function(message) {
                $("#projectbody").clear()
            }
        }
    )
}

function add_project_row(table, project) {
    let i = table.row.add([
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
    table.rows(i).nodes().to$().attr("data-oid",project["_id"]["$oid"])

}

function load_initial_content() {
    
    $("#maincontent").show()
    
    // Get their list of projects
    update_projects()

    // Load the config
    load_configuration()

}
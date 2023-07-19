
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

                    // Update the groups
                    let s = $("#person_group")
                    s.empty()
                    configuration.groups.sort()
                    for (let i in configuration.groups) {
                        s.append(`<option>${configuration.groups[i]}</option>`)
                    }
                },
                error: function(message) {
                    console.log("Failed to retrieve configuration")
                }
            }
        )
    }

}


function new_person() {
    // Clear any stored values
    $("#person_first_name").val("")
    $("#person_last_name").val("")
    $("#person_group").val("")
    $("#person_username").val("")
    $("#person_password").val("")
    $("#person_admin").prop('checked', false)
    $("#newpersondiv").modal("show")
}


function edit_person() {
        // We just grab the oid from the table.  The event comes from the button
        // so we need to go up to the td then up again to the tr where the oid is
        let table = $("#persontable").DataTable()
        let row = $(this).parent().parent()
        let oid = row.data("oid")
        let row_data = table.row(row).data()

        $("#person_first_name").val(row_data[1])
        $("#person_last_name").val(row_data[2])
        $("#person_group").val(row_data[3])
        $("#person_username").val(row_data[0])
        $("#person_password").val("")
        $("#person_admin").prop('checked', row_data[4])
        $("#newpersondiv").modal("show")

        // We also add the person's oid to the submit button on the
        // form so that when it's clicked we know that this is an 
        // update instead of a new person
        $("#create_person").data("oid",oid)    
}

function create_person () {

    // Collect the information we need
    // TODO: Do something sensible if they haven't given everything
    let first_name = $("#person_first_name").val()
    let last_name = $("#person_last_name").val()
    let group = $("#person_group").val()
    let username = $("#person_username").val()
    let password = $("#person_password").val()
    let admin = $("#person_admin").is(':checked')

    // We also look for an oid on the submit button.  If we
    // find one then we are doing an edit rather than a 
    // create
    let oid = $(this).data("oid")

    // Clear the data on the submit button
    $(this).removeData("oid")

    $.ajax(
        {
            url: backend,
            method: "POST",
            data: {
                action: "new_person",
                session: session,
                oid: oid,
                first_name: first_name,
                last_name: last_name,
                group: group,
                username: username,
                password: password,
                admin: admin
            },
            success: function(new_person_details) {

                // Add this to the list of people and show its details
                let t = $('#persontable').DataTable();

                // Remove a row if it already exists for this oid
                t.row($("tr[data-oid='"+new_person_details["_id"]["$oid"]+"']")).remove()

                // Add the new row
                add_person_row(t,new_person_details)

                // Redraw the table
                t.draw()

                // Update the events
                $(".editperson").unbind()
                $(".editperson").click(edit_person)

                // Remove the new person dialog
                $("#newpersondiv").modal("hide")

            },
            error: function(message) {
                console.log("Failed to create person")
            }
        }
    )
}

function update_people(){

    $.ajax(
        {
            url: backend,
            method: "POST",
            data: {
                action: "list_people",
                session: session
            },
            success: function(people) {
                $("#personbody").empty()

                let t = $('#persontable').DataTable();
                t.clear()

                for (let p in people) {
                    let person = people[p]
                    add_person_row(t,person)
                }

                t.draw()
                $(".editperson").unbind()
                $(".editperson").click(edit_person)
            },
            error: function(message) {
                $("#personbody").clear()
            }
        }
    )
}

function add_person_row(table, person) {
    let i = table.row.add([
        person["username"],
        person["first_name"],
        person["last_name"],
        person["group"],
        person["admin"],
        "<button class='btn btn-primary editperson'>Edit</button>",
        "<button class='btn btn-danger deleteperson'>Disable</button>"
    ]).index();

    // Now we can add the project oid to the tr as a 
    // data attribute so we can find the project oid
    // easily when someone clicks on it.
    table.rows(i).nodes().to$().attr("data-oid",person["_id"]["$oid"])

}

function load_initial_content() {
    
    $("#maincontent").show()
    
    // Get their list of projects
    update_people()

    // Load the config
    load_configuration()

}

function close_content() {
    $("#maincontent").hide()
    $('#persontable').DataTable().rows().remove()
}

function initial_setup () {
    $("#persontable").DataTable()

    // Action for starting a new person
    $("#newperson").click(new_person)

    // Action for submitting a new person
    $("#create_person").click(create_person)
    
}
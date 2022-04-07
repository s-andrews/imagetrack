
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
    $("#person_email").val("")
    $("#person_password").val("")
    $("#person_admin").prop('checked', false)
    $("#newpersondiv").modal("show")
}


function edit_person() {
        console.log(this)
        // We just grab the oid from the table.
        let oid = $(this).data("oid")
    
}

function create_person () {

    // Collect the information we need
    // TODO: Do something sensible if they haven't given everything
    let first_name = $("#person_first_name").val()
    let last_name = $("#person_last_name").val()
    let group = $("#person_group").val()
    let email = $("#person_email").val()
    let password = $("#person_password").val()
    let admin = $("#person_admin").val()

    $.ajax(
        {
            url: backend,
            method: "POST",
            data: {
                action: "new_person",
                session: session,
                first_name: first_name,
                last_name: last_name,
                group: group,
                email: email,
                password: password,
                admin: admin
            },
            success: function(new_person_details) {

                // Add this to the list of people and show its details
                let t = $('#persontable').DataTable();
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
                console.log(people)
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
        person["email"],
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
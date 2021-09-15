var nav_file_dict = {
    'sequencer.html': 'Sequencer',
    'index.html': 'Carrier PCB Control'
}

function get_navbar(document_name) {
    // return  ('<p>Your document is called ' + document_name + '</p>');
    var nav = '';
    // nav += '<nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">';
    nav += '<nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">';
    nav += '    <div class="navbar-nav">';
    nav += '        <a class="navbar-brand" href="#">ODIN</a>';

    console.log(nav_file_dict);
    console.log(Object.keys(nav_file_dict));
    for (const [current_filename, current_heading] of Object.entries(nav_file_dict)) {
        console.log('adding filename ' + current_filename + 'heading' + current_heading);
        nav += '        <li class="nav-item">';

        let active_text = '';
        if (current_filename == document_name) {
            console.log('This is the active document');
            active_text = 'active';
        } else {
            active_text = '';
        }
        nav += '            <a class="nav-link' + active_text + '" href="' + current_filename + '">' + current_heading + '</a>';

        nav += '        </li>';
    }

    nav += '    </div>';
    nav += '</nav>';
    
    return nav;
};
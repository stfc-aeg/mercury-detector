/* Local page links with their titles in the navbar. Comment out to
 * remove a page from appearing in the bar.
 */
var nav_file_dict = {
    // 'sequencer.html': 'Sequencer',
    // 'index.html': 'Carrier PCB Control'
}

/* Static links that will be included in the bar, to be opened in a
 * new tab on click
 */
var nav_repo_links = {
    'https://github.com/odin-detector': 'odin-detector',
    'https://github.com/stfc-aeg/mercury-detector': 'mercury-detector',
    'https://github.com/stfc-aeg/loki': 'LOKI'
}

/* Returns html for a global navigation bar. Will list pages with
 * titles as defined in nav_file_dict. If the document_name supplied
 * matches a file name, it will be highlighted as active to indicate
 * current location. If there is no match, there will be no
 * highlighted page. Therefore supplying null will return a basic
 * navbar with still working links.
 */
function get_navbar(document_name) {
    // return  ('<p>Your document is called ' + document_name + '</p>');
    var nav = '';
    // nav += '<nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">';
    nav += '<nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">';
    nav += '    <div class="navbar-nav">';
    nav += `
                <a class="navbar-brand" href="#">
                   <img src="https://avatars.githubusercontent.com/u/28647980?s=200&v=4" alt="" width="30" height="24" class="d-inline-block align-text-top">
                    ODIN
                </a>
    `;

    /* Adding page links */
    // console.log(nav_file_dict);
    // console.log(Object.keys(nav_file_dict));
    for (const [current_filename, current_heading] of Object.entries(nav_file_dict)) {
        // console.log('adding filename ' + current_filename + 'heading' + current_heading);
        nav += '    <li class="nav-item">';

        let active_text = '';
        if (current_filename == document_name) {
            // console.log('This is the active document');
            active_text = 'active';
        } else {
            active_text = '';
        }
        nav += '        <a class="nav-link' + active_text + '" href="' + current_filename + '">' + current_heading + '</a>';

        nav += '    </li>';
    }

    /* Adding static links */
    nav += `
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="navbarDropdownMenuLink" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                            Repositories
                        </a>
                        <ul class="dropdown-menu" aria-labelledby="navbarDropdownMenuLink">
    `;
    for (const [current_link, current_heading] of Object.entries(nav_repo_links)) {
        nav += '            <li class="nav-item">';
        nav += '                <a class="dropdown-item" href="' + current_link + '" target="_blank">' + current_heading + '</a>';
        nav += '            </li>';
    }
    nav += `
                        </ul>
                    </li>
    `;

    nav += '    </div>';
    nav += '</nav>';
    
    return nav;
};

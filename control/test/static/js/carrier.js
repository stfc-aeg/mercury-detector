api_version = '0.1';
// adapter_name = 'loki';
adapter_name = 'carrier';
ajax_timeout_ms = 1000;

$( document ).ready(function() {

    // Init UI
    init();

    update_api_version();
    update_api_adapters();

    // Loki additions
    update_loki_ff_static_data();
    poll_loki();
    poll_loki_vregneeded();
    poll_loki_slow();
});

let carrier_endpoint;
function init() {

    // Generate the Adatper Endpoint for get/put requests
    carrier_endpoint = new AdapterEndpoint(adapter_name, api_version);

    // Generate the firefly channel switches
    document.getElementById('ff1_chtable').innerHTML = generateFireFlyChannelTable(1,
        12,     // 12 Channels
        2,      // Arrange in 3 columns
        false); // Do not include additional state column (indicated by switch)
    generateFireFlyChannelSwitches(1, 12);
    document.getElementById('ff2_chtable').innerHTML = generateFireFlyChannelTable(2,
        12,     // 12 Channels
        2,      // Arrange in 3 columns
        false); // Do not include additional state column (indicated by switch)
    generateFireFlyChannelSwitches(2, 12);

    init_power_tracking();
    init_environment_tracking();
    create_load_chart();

    $('#power-cycle-spinner').hide()
}

function update_api_version() {
    $.ajax({url:'/api/',
        async: true,
        dataType: 'json',
        timeout: ajax_timeout_ms,
        success: function(response, textStatus, requestObj) {
            $('#api-version').html(response.api);
            api_version = response.api;
        }
    });
}

function update_api_adapters() {
    $.ajax({url:'/api/' + api_version + '/adapters/',
        async: true,
        dataType: 'json',
        timeout: ajax_timeout_ms,
        success: function(response, textStatus, requestObj) {
            adapter_list = response.adapters.join(", ");
            $('#api-adapters').html(adapter_list);
        }
    });
}

function poll_loki_vregneeded() {
	// Poll functions that require vreg enabled. This means the timeout will not
	// slow the response of other updates

    Promise.allSettled([
        new Promise((resolve) => { update_loki_ff_data(); }),
        new Promise((resolve) => { update_loki_power_monitor(); }),
        new Promise((resolve) => { update_loki_asic_cal_pattern_en(); }),
        new Promise((resolve) => { update_loki_asic_preamp(); }),
        new Promise((resolve) => { update_loki_asic_integration_time(); }),
        new Promise((resolve) => { update_loki_asic_frame_length(); }),
        new Promise((resolve) => { update_loki_asic_serialiser_mode(); }),
        new Promise((resolve) => { update_loki_asic_segment_readout(); }),
    ]);

	setTimeout(poll_loki_vregneeded, 1000);
}

function poll_loki() {
    Promise.allSettled([
        new Promise((resolve) => { update_loki_vreg_en(); }),
        new Promise((resolve) => { update_loki_asic_nrst(); }),
        new Promise((resolve) => { update_loki_vcal(); }),

        new Promise((resolve) => { update_loki_asic_sync_aux(); }),    // Call before sync
        new Promise((resolve) => { update_loki_asic_sync(); }),

        new Promise((resolve) => { update_loki_connection(); }),
        new Promise((resolve) => { update_loki_performance(); }),
        new Promise((resolve) => { update_loki_critical_temp(); }),
    ]);

	setTimeout(poll_loki, 1000);
}

function poll_loki_slow() {
	/* Items that change slowly, to avoid pointlessly quick refresh */
	new Promise((resolve) => { update_loki_temps(); });		// Bus interaction every call

	setTimeout(poll_loki_slow, 4000);
}

function set_chart_animation_duration(duration) {
    chart_vol.options.animation.duration = duration
    chart_cur.options.animation.duration = duration
    chart_temp.options.animation.duration = duration
    chart_hum.options.animation.duration = duration

    const d = new Date();
    exdays = 30;    // Keep this cookie for 30 days
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    let expires = "expires="+d.toUTCString();
    document.cookie = "chartAnimationDuration="+duration.toString()+";"+expires+";path=/;SameSite=Strict;";
}

function get_chart_animation_duration() {
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    let name = "chartAnimationDuration=";
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
		while (c.charAt(0) == ' ') {
          c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
          return parseInt(c.substring(name.length, c.length));
        }
    }
    return 1000;  // Default duration if no cookie is found
}

var chart_vol;
var chart_cur;
function init_power_tracking() {
    var chart_element = document.getElementById("voltage-chart").getContext('2d');
    chart_vol = new Chart(chart_element,
    {
        type: 'line',
        yAxisID: 'Rail Voltage /V',
        data: {
            labels: power_tracking_time,
            datasets: [{
                label: "Digital",
                data: power_tracking_data_dig_V,
                backgroundColor: ['rgba(255, 0, 0, .2)'],
                spanGaps: false
                },
                {
                label: "Digital Control",
                data: power_tracking_data_digctrl_V,
                backgroundColor: ['rgba(0, 0, 255, .2)'],
                },
                {
                label: "Analogue",
                data: power_tracking_data_analogue_V,
                backgroundColor: ['rgba(0, 255, 0, .2)'],
                }
            ]
        },
        options: {
            animation: {
                duration: get_chart_animation_duration(),
            },
            responsiveAnimationDuration: 0,
            elements: {
                line: {
                    tension: 0
                    }
            },
            //responsive: true,
	    scales: {
	        xAxes: [{
                    type: 'time',
		    distribution: 'linear',
		    ticks: {
	                source: 'data',
		    }
		}]
	    }
        }
    });

    var chart_element = document.getElementById("current-chart").getContext('2d');
    chart_cur = new Chart(chart_element,
    {
        type: 'line',
        yAxisID: 'Rail Current /A',
        data: {
            labels: power_tracking_time,
            datasets: [{
                label: "Digital",
                data: power_tracking_data_dig_I,
                backgroundColor: ['rgba(255, 0, 0, .2)'],
                },
                {
                label: "Digital Control",
                data: power_tracking_data_digctrl_I,
                backgroundColor: ['rgba(0, 0, 255, .2)'],
                },
                {
                label: "Analogue",
                data: power_tracking_data_analogue_I,
                backgroundColor: ['rgba(0, 255, 0, .2)'],
                }
            ]
        },
        options: {
            animation: {
                duration: get_chart_animation_duration(),
            },
            responsive: true,
            responsiveAnimationDuration: 0,
            elements: {
                line: {
                    tension: 0
                    }
            },
	    scales: {
	        xAxes: [{
                    type: 'time',
		    distribution: 'linear',
			ticks: {
	                source: 'data',
		    }
		}]
	    }
        }
    });
}

var chart_temp;
var chart_hum;
function init_environment_tracking() {
    var chart_element = document.getElementById("temperature-chart").getContext('2d');
    chart_temp = new Chart(chart_element,
    {
        type: 'line',
        yAxisID: 'Temperature /C',
        data: {
            labels: environment_tracking_time,
            datasets: [{
                label: "Case",
                data: environment_tracking_data_case_temp,
                backgroundColor: ['rgba(255, 0, 0, .2)'],
                spanGaps: false
                },
                {
                label: "PT100",
                data: environment_tracking_data_pt100_temp,
                backgroundColor: ['rgba(0, 0, 255, .2)'],
                },
                {
                label: "ASIC Diode",
                data: environment_tracking_data_asic_diode_temp,
                backgroundColor: ['rgba(0, 255, 0, .2)'],
                }
            ]
        },
        options: {
            animation: {
                duration: get_chart_animation_duration(),
            },
            responsiveAnimationDuration: 0,
            elements: {
                line: {
                    tension: 0
                    }
            },
            //responsive: true,
	    scales: {
	        xAxes: [{
                    type: 'time',
		    distribution: 'linear',
		    ticks: {
	                source: 'data',
		    }
		}]
	    }
        }
    });

    var chart_element = document.getElementById("humidity-chart").getContext('2d');
    chart_hum = new Chart(chart_element,
    {
        type: 'line',
        yAxisID: 'Relative Humidity /%',
        data: {
            labels: environment_tracking_time,
            datasets: [{
                label: "Case",
                data: environment_tracking_data_case_humidity,
                backgroundColor: ['rgba(255, 0, 0, .2)'],
                }
            ]
        },
        options: {
            animation: {
                duration: get_chart_animation_duration(),
            },
            responsive: true,
            responsiveAnimationDuration: 0,
            elements: {
                line: {
                    tension: 0
                    }
            },
	    scales: {
	        xAxes: [{
                    type: 'time',
            animation: {
                duration: get_chart_animation_duration(),
            },
		    distribution: 'linear',
			ticks: {
	                source: 'data',
		    }
		}]
	    }
        }
    });
}

function generateFireFlyChannelSwitches(id, num_channels) {
    // Initialise the table switches
    for (channel_num = 0; channel_num < num_channels; channel_num++) {
        switchname = "[name='firefly-"+id+"-CH"+channel_num+"-switch']";
        switchname = "firefly-"+id+"-CH"+channel_num+"-switch";
        //console.log("init switchname " + switchname);
        $("[name='"+switchname+"']").bootstrapSwitch();
        $("[name='"+switchname+"']").bootstrapSwitch('onText', 'Enabled');
        $("[name='"+switchname+"']").bootstrapSwitch('offText', 'Disabled');
        $("[name='"+switchname+"']").bootstrapSwitch('offColor', 'danger');
        $("[name='"+switchname+"']").bootstrapSwitch('disabled', false);
        //$("input[name='"+switchname+"']").on('switchChange.bootstrapSwitch', function(event,state) {
        $("[name='"+switchname+"']").bootstrapSwitch('onSwitchChange', callback_FireFly_Channel_Switches);
    }
}

function callback_FireFly_Channel_Switches(event, state) {
    target_switchname = event.target.name;
    target_ff_id = parseInt(target_switchname.split("-")[1]);
    target_channelname = parseInt(target_switchname.split("-")[2].substring(2));
    console.log("Running callback for firefly "+target_ff_id+" CH"+target_channelname + " with name " + target_switchname);

    if ($("[name='"+target_switchname+"']").bootstrapSwitch('disabled')) {
        console.log("FF"+target_ff_id+" CH"+target_channelname+": Ignoring change of state when disabled");
    } else {
        console.log("FF"+target_ff_id+" CH"+target_channelname+": switch fired with disable state " + !state);
        //console.log(event);
        ff = target_ff_id;
        ch = target_channelname;
        change_ff_ch_dis(!state, ff, ch);
        $("[name='"+target_switchname+"']").bootstrapSwitch('disabled', true);
    }
}

function callback_FireFly_Channel_GlobalState_Button(ff_id, num_channels, en) {
    console.log("Setting all firefly " + ff_id + " channels " + en);

    for (ff_ch = 0; ff_ch < num_channels; ff_ch++) {
        switchname = 'firefly-'+ff_id+'-CH'+ff_ch+'-switch';
        if (en) {
            $('[name=' + switchname + ']').bootstrapSwitch('state', true);
        } else {
            $('[name=' + switchname + ']').bootstrapSwitch('state', false);
        }
    }
}

function generateFireFlyChannelTable(id, num_channels, num_cols, en_state_col) {
    /* en_state_col will generate an additional column for channel state. However, this should be
     * covered by the switch state. */

    // The channel column is 20% of the channel-toggle width
    chcol_width = 20 / num_cols;

    // Create the HTML
    var ret = `
                    <div class="row contflex">
                        <div class="col-8 col-md-8">
                            <p>Manufacturer:&nbsp;
                                <span id="firefly-${id}-venid">&nbsp;</span>
                                , Product: 
                                <span id="firefly-${id}-prodid">&nbsp;</span>
                            </p>
                        </div>
                        <div class="col-4 col-md-4">
                            <button type="button" class="btn btn-primary btn-sm" id="firefly-${id}-allon-button" onclick="callback_FireFly_Channel_GlobalState_Button(${id}, ${num_channels}, true)">Enable All</button>
                            <button type="button" class="btn btn-danger btn-sm" id="firefly-${id}-alloff-button" onclick="callback_FireFly_Channel_GlobalState_Button(${id}, ${num_channels}, false)">Disable All</button>
                        </div>
                    </div>
                    <div class = "row">
                        <table class="table table-striped"style="width=50%">
                            <thead>
                                <tr>
                `;

    for (let column_num = 0; column_num < num_cols; column_num++) {
        ret += `
                                    <th style="width:${chcol_width}%">Chan</th>
                                    <th>State Toggle</th>
                `;
        if (en_state_col) {
            ret += `
                                    <th>State</th>
                    `;
        }
    }

    ret += `
                                </tr>
                            </thead>
                            <tbody>
            `;

    for (channel_num = 0; channel_num < num_channels; channel_num++) {
        if (channel_num % num_cols == 0) {/* Leftmost column */
            ret += `
                                <tr>
                    `;
        }

        ret += `
                                    <td>CH${channel_num}</td>
                                    <td>
                                        <input type="checkbox" name="firefly-${id}-CH${channel_num}-switch" data-size="small">
                                    </td>
                `;
        if (en_state_col) {
            ret += `
                                    <td><span id="firefly-${id}-CH${channel_num}-dis">&nbsp;</span></td>
                `;
        }

        if (((channel_num + 1) % num_cols == 0) || /* Rightmost column */
            ((channel_num + 1) == num_channels)) {  /* Last column */
            ret += `
                                </tr>
                    `;
        }
    }

    ret += `
                            </tbody>
                        </table>
                    </div>
                    `;
    return ret;
}


var any_firefly_present = false;
async function update_loki_ff_static_data() {
    // FireFly General Information
    // await is used so that loop variables are valid when callback operates
    for (let ff_id = 1; ff_id <=2; ff_id++) {
        var firefly_vendorid = "";
        var firefly_product = "";

        // Vendor ID
        await carrier_endpoint.get('FIREFLY'+ff_id+'/VENDORID', timeout=ajax_timeout_ms)
        .then(response => {
            any_firefly_present = true;
            firefly_vendorid = response.VENDORID;
            //console.log("Got FireFly VendorID: "+firefly_vendorid);
            $('#firefly-'+ff_id+'-venid').html(firefly_vendorid);
            $('#firefly-'+ff_id+'-venid').removeClass();
            $('#firefly-'+ff_id+'-venid').addClass("badge bg-info");
        })
        .catch(error => {
            // If there is no response to from the FireFly query, indicate this
            $('#firefly-'+ff_id+'-venid').html('NO RESPONSE');
            $('#firefly-'+ff_id+'-venid').removeClass();
            $('#firefly-'+ff_id+'-venid').addClass("badge bg-warning");
        });

        // Part Number
        await carrier_endpoint.get('FIREFLY'+ff_id+'/PARTNUMBER', timeout=ajax_timeout_ms)
        .then(response => {
            firefly_product = response.PARTNUMBER;
            console.log(document.getElementById('firefly-'+ff_id+'-prodid'));
            $('#firefly-'+ff_id+'-prodid').html(firefly_product);
            $('#firefly-'+ff_id+'-prodid').removeClass();
            $('#firefly-'+ff_id+'-prodid').addClass("badge bg-info");
        })
        .catch(error => {
            // If there is no response to from the FireFly query, indicate this
            $('#firefly-'+ff_id+'-prodid').html('NO RESPONSE');
            $('#firefly-'+ff_id+'-prodid').removeClass();
            $('#firefly-'+ff_id+'-prodid').addClass("badge bg-warning");
        });
    }
}

var any_firefly_channel_down = [false, false];  // ff1, ff2
async function update_loki_ff_data() {

	// Channel States
    for (let ff_id = 1; ff_id <=2; ff_id++) {
        await carrier_endpoint.get('FIREFLY'+ff_id+'/CHANNELS', timeout=ajax_timeout_ms)
        .then(response => {
            // FireFly Disabled Channels
            var firefly_ch_dis = response.CHANNELS;
            var firefly_ch_dis_ch0 = response.CHANNELS.CH0.Disabled;
            var channel_states = "";

            any_firefly_channel_down[ff_id-1] = false;
            for (const [key, value] of Object.entries(firefly_ch_dis)) {
                if (value.Disabled) any_firefly_channel_down[ff_id-1] = true;
                //console.log(value);
                channel_states = channel_states.concat(" " + key + ": " + value.Disabled);

                $('#firefly-'+ff_id+'-'+key+'-dis').html(value.Disabled ? "Disabled" : "Enabled");

                // Rewrite and enable the channel switches
                button_target_disabled_state = !$("[name='firefly-"+ff_id+"-"+key+"-switch']").bootstrapSwitch('state');
                if (button_target_disabled_state != value.Disabled) {
                    //console.log("CH " +key+ " Value not yet updated");
                    $("[name='firefly-"+ff_id+"-"+key+"-switch']").bootstrapSwitch('state', !(value.Disabled), true);
                } else {
                    //console.log("CH " +key+ " Value now at target");
                    $("[name='firefly-"+ff_id+"-"+key+"-switch']").bootstrapSwitch('state', !(value.Disabled));
                    $("[name='firefly-"+ff_id+"-"+key+"-switch']").bootstrapSwitch('disabled', false);
                }
            }
            $('#firefly-'+ff_id+'-ch-dis').html(channel_states);
        })
        .catch(error => {
            // If there is no response from the firefly query, disable the channel switches
            for (channel_num = 0; channel_num < 12; channel_num++) {
                $("[name='firefly-"+ff_id+"-CH"+channel_num+"-switch']").bootstrapSwitch('disabled', true);
            }

            // Only bother to print out the read error if the fireflies are actually present
            if (any_firefly_present) {
                console.log('Error getting Firefly ' + ff_id + ' channels: ' + error);
            }
        });
    }

    // If there is no firefly to control, indicate this and disable the
    // button. Otherwise enable the global enable button
    //console.log('Any FireFly present: ' + any_firefly_present);
    //console.log('Any FireFly channel down: ' + any_firefly_channel_down);
    if (any_firefly_present) {
        // If any of the channels is down while at least one firefly
        // is present, indicate this to propmpt the user to enable.
        if (any_firefly_channel_down[0] || any_firefly_channel_down[1]) {
            $('#all-ff-down-state').html("At least one disabled");
            $('#all-ff-down-state').removeClass();
            $('#all-ff-down-state').addClass("badge bg-danger");
            $('#firefly-global-allon-button').removeClass("disabled");
        } else {
            $('#all-ff-down-state').html("All Enabled");
            $('#all-ff-down-state').removeClass();
            $('#all-ff-down-state').addClass("badge bg-success");
            $('#firefly-global-allon-button').addClass("disabled");
        }
        $('#firefly-global-alloff-button').removeClass("disabled");
    } else {
        $('#all-ff-down-state').html("No FireFly");
        $('#all-ff-down-state').removeClass();
        $('#all-ff-down-state').addClass("badge bg-warning");
        $('#firefly-global-allon-button').addClass("disabled");
        $('#firefly-global-alloff-button').addClass("disabled");
    }
}

var latest_asic_temp =null;		// Latest asic temperature
var environment_tracking_data_case_temp = [];
var environment_tracking_data_pt100_temp = [];
var environment_tracking_data_asic_diode_temp = [];
var environment_tracking_data_case_humidity = [];
var environment_tracking_time = [];
var environment_tracking_valuelimit = 40;
async function update_loki_temps() {
    var temp_ambient = NaN;
    var temp_pt100 = NaN;
    var temp_asic = NaN;
    var hum_ambient = NaN;

	// FireFly Temperatures
    for (let ff_id = 1; ff_id <=2; ff_id++) {
        // Use await to force synchronous call, meaning loop variables will be valid for callback
        await carrier_endpoint.get('FIREFLY'+ff_id+'/TEMPERATURE', timeout=ajax_timeout_ms)
        .then(response => {
            if (response.TEMPERATURE != null) {
                var firefly_temp = response.TEMPERATURE.toFixed(2);
                //console.log("FireFly "+ff_id_recovered+" temperature: "+firefly_temp);
                $('#temp-firefly'+ff_id).html(firefly_temp);
            } else {
                $('#temp-firefly'+ff_id).html('No Con');
            }
        })
        .catch(error => {
            $('#temp-firefly'+ff_id).html("N/A");

            // Only bother to print out the read error if the fireflies are actually present
            if (any_firefly_present) {
                console.log('failed to get temperature for ff id ' + ff_id + ': ' + error)
            }
        });
    }

	// Other System Temperatures
    carrier_endpoint.get('TEMPERATURES', timeout=ajax_timeout_ms)
    .then(response => {
        //console.log(response.TEMPERATURES);

        // Ambient Temperature
            if (response.TEMPERATURES.AMBIENT != null) {
            temp_ambient = response.TEMPERATURES.AMBIENT.toFixed(2);
            $('#temp-ambient').html(temp_ambient);
            //latest_asic_temp = temp_ambient;  //TODO TEMPORARY
        } else {
            $('#temp-ambient').html('No Con');
        }

        // Ambient Humidity (TODO MOVE)
            if (response.TEMPERATURES.HUMIDITY != null) {
                hum_ambient = response.TEMPERATURES.HUMIDITY.toFixed(2);
                //console.log('Humidity ' + hum_ambient);
                $('#hum-ambient').html(hum_ambient);
                //latest_asic_temp = temp_ambient;  //TODO TEMPORARY
            } else {
                $('#hum-ambient').html('No Con');
            }

        // PT100 Temperature
        if (response.TEMPERATURES.PT100 != null) {
            temp_pt100 = response.TEMPERATURES.PT100.toFixed(2);
            $('#temp-pt100').html(temp_pt100);
        } else {
            console.log('Failed to read PT100');
            $('#temp-pt100').html('FAIL');
        }

        // ASIC Temperature
        if (response.TEMPERATURES.ASIC != null) {
            //console.log('got an ASIC temperature: ' + response.TEMPERATURES.ASIC);
            temp_asic = response.TEMPERATURES.ASIC.toFixed(2);
            $('#temp-asic').html(temp_asic);
            latest_asic_temp = temp_asic;  //TODO TEMPORARY
        } else {
            //console.log('ASIC temperature was null');
            $('#temp-asic').html('FAIL (last ' + latest_asic_temp + ')');
        }

        // Update chart data
        environment_tracking_data_case_temp.push(temp_ambient);
        if (environment_tracking_data_case_temp.length > environment_tracking_valuelimit) environment_tracking_data_case_temp.shift();

        environment_tracking_data_pt100_temp.push(temp_pt100);
        if (environment_tracking_data_pt100_temp.length > environment_tracking_valuelimit) environment_tracking_data_pt100_temp.shift();

        environment_tracking_data_asic_diode_temp.push(temp_asic);
        if (environment_tracking_data_asic_diode_temp.length > environment_tracking_valuelimit) environment_tracking_data_asic_diode_temp.shift();

        environment_tracking_data_case_humidity.push(hum_ambient);
        if (environment_tracking_data_case_humidity.length > environment_tracking_valuelimit) environment_tracking_data_case_humidity.shift();

        dt = new Date();
        environment_tracking_time.push(
        dt.toISOString()
        );
        if (environment_tracking_time.length > environment_tracking_valuelimit) environment_tracking_time.shift();

        chart_temp.update();
        chart_hum.update();
    })
    .catch(error => {
        console.log('PCB Temperature reading error: ' + error);
    });

	// LOKI System Temperature
    carrier_endpoint.get('LOKI_PERFORMANCE/TEMPERATURES', timeout=ajax_timeout_ms)
    .then(response => {
        // Zynq PS Temperature
            if (response.TEMPERATURES.PS != null) {
            var temp_zynqps = response.TEMPERATURES.PS.toFixed(2);
            $('#temp-zynqps').html(temp_zynqps);
        } else {
            $('#temp-ambient').html('No Con');
        }
    })
    .catch(error => {
        console.log('LOKI Temperature reading error: ' + error);
	});
}

var loki_load_data = [];
function create_load_chart() {
    var chart_element = document.getElementById("loki-load-chart").getContext('2d');

    var data = {
        labels: ['1m', '5m', '15m'],
        datasets: [{
              label: 'LOKI Load',
              data: loki_load_data,
              backgroundColor: [
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                        'rgba(153, 102, 255, 0.2)',
                      ],
              borderColor: [
                        'rgb(75, 192, 192)',
                        'rgb(54, 162, 235)',
                        'rgb(153, 102, 255)',
                      ],
              borderWidth: 1
            }]
    };

    chart_load = new Chart(chart_element,
    {
        type: 'bar',
        yAxisID: 'Load',
        data: data,
        options: {
            animation: {
                duration: get_chart_animation_duration(),
            },
            responsiveAnimationDuration: 0,
            elements: {
                line: {
                    tension: 0
                    }
            },
            //responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    //chart_load.update();
}

function update_loki_performance() {
    carrier_endpoint.get('LOKI_PERFORMANCE', timeout=ajax_timeout_ms)
    .then(response => {
        // Memory
        var total_mem = 0;
        // Memory
        if (response.LOKI_PERFORMANCE.MEM != null) {
            total_mem = response.LOKI_PERFORMANCE.MEM.TOTAL.toFixed(2);
        } else {
        }

        if (response.LOKI_PERFORMANCE.MEM != null) {
            var freemem = response.LOKI_PERFORMANCE.MEM.FREE.toFixed(2);
            var freemem_perc = (freemem / total_mem) * 100;
            //console.log('free memory percentage: ' + freemem_perc);
            document.getElementById("loki-mem-free").style.width=freemem_perc + "%";
            document.getElementById("loki-mem-free").innerHTML=parseInt(freemem / (1024*1024)) + "MB free";
        } else {
            document.getElementById("loki-mem-free").style.width="0%";
        }

        if (response.LOKI_PERFORMANCE.MEM != null) {
            var availmem = response.LOKI_PERFORMANCE.MEM.AVAILABLE.toFixed(2);
            var availmem_perc = (availmem / total_mem) * 100;
            //console.log('available memory percentage: ' + availmem_perc);
            document.getElementById("loki-mem-avail").style.width=availmem_perc + "%";
            document.getElementById("loki-mem-avail").innerHTML=parseInt(availmem / (1024*1024)) + "MB available";
        } else {
            document.getElementById("loki-mem-avail").style.width="0%";
        }


        // Load
        if (response.LOKI_PERFORMANCE.LOAD != null) {
            loki_load_data = response.LOKI_PERFORMANCE.LOAD;
            chart_load.data.datasets[0].data = loki_load_data;
            //console.log(loki_load_data);
            chart_load.update();
        }
    })
    .catch(error => {
        console.log('LOKI Temperature reading error: ' + error);
    });
}

var power_tracking_data_dig_V = [];
var power_tracking_data_digctrl_V = [];
var power_tracking_data_analogue_V = [];
var power_tracking_data_dig_I = [];
var power_tracking_data_digctrl_I = [];
var power_tracking_data_analogue_I = [];
var power_tracking_time = [];

var power_tracking_valuelimit = 20;

function update_loki_power_monitor() {
	var psu_analogue_pwr = NaN;
	var psu_dig_pwr = NaN;
	var psu_dig_ctrl_pwr = NaN;
	var psu_analogue_vol = NaN;
	var psu_dig_vol = NaN;
	var psu_dig_ctrl_vol = NaN;
	var psu_analogue_cur = NaN;
	var psu_dig_cur = NaN;
	var psu_dig_ctrl_cur = NaN;

    carrier_endpoint.get('PSU', timeout=ajax_timeout_ms)
    .then(response => {
        try {psu_analogue_pwr = response.PSU.ANALOGUE.POWER.toFixed(5);} catch (TypeError) {}
        try {psu_dig_pwr = response.PSU.DIG.POWER.toFixed(5);} catch (TypeError) {}
        try {psu_dig_ctrl_pwr = response.PSU.DIG_CTRL.POWER.toFixed(5);} catch (TypeError) {}
        $('#psu-analogue-pwr').html(psu_analogue_pwr);
        $('#psu-dig-pwr').html(psu_dig_pwr);
        $('#psu-dig-ctrl-pwr').html(psu_dig_ctrl_pwr);

        try {psu_analogue_vol = response.PSU.ANALOGUE.VOLTAGE.toFixed(5);} catch (TypeError) {}
        try {psu_dig_vol = response.PSU.DIG.VOLTAGE.toFixed(5);} catch (TypeError) {}
        try {psu_dig_ctrl_vol = response.PSU.DIG_CTRL.VOLTAGE.toFixed(5);} catch (TypeError) {}
        $('#psu-analogue-vol').html(psu_analogue_vol);
        $('#psu-dig-vol').html(psu_dig_vol);
        $('#psu-dig-ctrl-vol').html(psu_dig_ctrl_vol);

        try {psu_analogue_cur = response.PSU.ANALOGUE.CURRENT.toFixed(5);} catch (TypeError) {}
        try {psu_dig_cur = response.PSU.DIG.CURRENT.toFixed(5);} catch (TypeError) {}
        try {psu_dig_ctrl_cur = response.PSU.DIG_CTRL.CURRENT.toFixed(5);} catch (TypeError) {}
        $('#psu-analogue-cur').html(psu_analogue_cur);
        $('#psu-dig-cur').html(psu_dig_cur);
        $('#psu-dig-ctrl-cur').html(psu_dig_ctrl_cur);

        // Update chart data
        power_tracking_data_dig_V.push(psu_dig_vol);
        if (power_tracking_data_dig_V.length > power_tracking_valuelimit) power_tracking_data_dig_V.shift();
        power_tracking_data_digctrl_V.push(psu_dig_ctrl_vol);
        if (power_tracking_data_digctrl_V.length > power_tracking_valuelimit) power_tracking_data_digctrl_V.shift();
        power_tracking_data_analogue_V.push(psu_analogue_vol);
        if (power_tracking_data_analogue_V.length > power_tracking_valuelimit) power_tracking_data_analogue_V.shift();

        power_tracking_data_dig_I.push(psu_dig_cur);
        if (power_tracking_data_dig_I.length > power_tracking_valuelimit) power_tracking_data_dig_I.shift();
        power_tracking_data_digctrl_I.push(psu_dig_ctrl_cur);
        if (power_tracking_data_digctrl_I.length > power_tracking_valuelimit) power_tracking_data_digctrl_I.shift();
        power_tracking_data_analogue_I.push(psu_analogue_cur);
        if (power_tracking_data_analogue_I.length > power_tracking_valuelimit) power_tracking_data_analogue_I.shift();

        dt = new Date();
        power_tracking_time.push(
        dt.toISOString()
        );
        if (power_tracking_time.length > power_tracking_valuelimit) power_tracking_time.shift();

        chart_vol.update();
        chart_cur.update();
    })
    .catch(error => {
        console.log('Error retrieving power supply data: ' + error);
    });
}

function update_loki_vcal() {
    carrier_endpoint.get('VCAL', timeout=ajax_timeout_ms)
    .then(response => {
        vcal_voltage = response.VCAL;

        $('#vcal-voltage').html(vcal_voltage + "v");
        $('#vcal-voltage').removeClass();
        $('#vcal-voltage').addClass("badge bg-success");
			//console.log('updated vcal as ' + vcal_voltage);
    })
    .catch(error => {
        $('#vcal-voltage').html(("No Con"));
        $('#vcal-voltage').removeClass();
        $('#vcal-voltage').addClass("badge bg-warning");
            console.log('Error retrieving VCAL: ' + error);
    });
}

function update_loki_asic_nrst() {
    carrier_endpoint.get('ASIC_RST', timeout=ajax_timeout_ms)
    .then(response => {
        asic_rst_state = response.ASIC_RST;

        // Configure the reset state indicator
        if (asic_rst_state) {
            // Use spinner to draw attention
            spinner_html = '<div class="spinner-grow spinner-grow-sm" role="status"><span class="visually-hidden">Loading...</span></div>'
            $('#asic-rst-state').html(spinner_html +  " RESET " + spinner_html);
            $('#asic-rst-state').removeClass();
    	    $('#asic-rst-state').addClass("badge bg-danger");
        } else {
            $('#asic-rst-state').html("Enabled");
            $('#asic-rst-state').removeClass();
    	    $('#asic-rst-state').addClass("badge bg-success");
        }
            //console.log("Got asic reset state: " + asic_rst_state)

        // Impact other controls
        if (asic_rst_state) {
            // $('#collapseFrameControl').addClass('disabled');
        }

    })
    .catch(error => {
        $('#asic-rst-state').html(("No Con"));
        $('#asic-rst-state').removeClass();
        $('#asic-rst-state').addClass("badge bg-warning");
        console.log('Error retrieving ASIC reset state: ' + error);
    });
}

function update_loki_vreg_en() {
    carrier_endpoint.get('VREG_CYCLE', timeout=ajax_timeout_ms)
    .then(response => {
        vreg_en_state = response.VREG_CYCLE;
        $('#vreg-en-state').html((vreg_en_state ? "Enabled" : "Disabled"));
        $('#vreg-en-state').removeClass();
        $('#vreg-en-state').addClass((vreg_en_state ? "badge bg-success" : "badge bg-danger"));

        if (vreg_en_state == 1) {
            // The power cycle is now complete
            $('#power-cycle-spinner').hide()

            // Enable buttons that do not make sense when there is no power
            $('#button-power-down-regulators').removeClass("disabled");
            $('#button-en-global').removeClass("disabled");
        } else {
            // Disable buttons that do not make sense when there is no power
            $('#button-power-down-regulators').addClass("disabled");
            $('#button-en-global').addClass("disabled");
        }

    })
    .catch(error => {
        $('#vreg-en-state').html(("No Con"));
        $('#vreg-en-state').removeClass();
        $('#vreg-en-state').addClass("badge bg-warning");
        console.log('Error retrieving vreg_en state: ' + error);
    });
}

function update_loki_asic_preamp() {
    carrier_endpoint.get('ASIC_FEEDBACK_CAPACITANCE', timeout=ajax_timeout_ms)
    .then(response => {
        asic_feedback_capacitance_state = response.ASIC_FEEDBACK_CAPACITANCE;

        asic_feedback_allowed_values = ["0", "7", "14", "21"];
        if (asic_feedback_allowed_values.includes(asic_feedback_capacitance_state)) {
            // Update the badge
            $('#asic-feedback-capacitance-state').html((asic_feedback_capacitance_state + " fF"));
            $('#asic-feedback-capacitance-state').removeClass();
            $('#asic-feedback-capacitance-state').addClass("badge bg-success");

            // Update the selection box
            //TODO
        } else {
            $('#asic-feedback-capacitance-state').html(("No Con"));
            $('#asic-feedback-capacitance-state').removeClass();
            $('#asic-feedback-capacitance-state').addClass("badge bg-warning");
        }
    })
    .catch(error => {
        $('#asic-feedback-capacitance-state').html(("No Con"));
        $('#asic-feedback-capacitance-state').removeClass();
        $('#asic-feedback-capacitance-state').addClass("badge bg-warning");
        console.log('Error retrieving vreg_en state: ' + error);
    });
}

function update_loki_asic_integration_time() {
    carrier_endpoint.get('ASIC_INTEGRATION_TIME', timeout=ajax_timeout_ms)
    .then(response => {
        integration_time = response.ASIC_INTEGRATION_TIME;

        // Update the badge
        $('#asic-integration-time-state').html((integration_time + " frame" + ((integration_time == 1) ? "" : "s")));
        $('#asic-integration-time-state').removeClass();
        $('#asic-integration-time-state').addClass("badge bg-success");
    })
    .catch(error=> {
        $('#asic-integration-time-state').html(("No Con"));
        $('#asic-integration-time-state').removeClass();
        $('#asic-integration-time-state').addClass("badge bg-warning");
        console.log('Error retrieving vreg_en state: ' + error);
    });
}

function en_dis_segment_vminmax(checked) {
    if (checked == true) {
        console.log('disabling vminmax entry');
        document.getElementById("segment-readout-vmin").setAttribute('disabled', '');
        document.getElementById("segment-readout-vmax").setAttribute('disabled', '');
    } else {
        console.log('enabling vminmax entry');
        document.getElementById("segment-readout-vmin").removeAttribute('disabled');
        document.getElementById("segment-readout-vmax").removeAttribute('disabled');
    }
}
var segment_new_capture = true
function trigger_segment_readout(segment, vmin, vmax, auto) {
    if (auto == true) {
        vmin = -1;
        vmax = -1;
    };

    carrier_endpoint.put(parseInt(vmin), 'ASIC_SEGMENT_VMIN', timeout=ajax_timeout_ms)
    .then((response) => carrier_endpoint.put(parseInt(vmax), 'ASIC_SEGMENT_VMAX', timeout=ajax_timeout_ms))
    .then((response) => carrier_endpoint.put(parseInt(segment), 'ASIC_SEGMENT_CAPTURE', timeout=ajax_timeout_ms))
    .then((response) => {
		console.log("Segment capture started for segment " + segment + " using colour range " + vmin + " to " + vmax);
        document.getElementById("segment-img").style="-webkit-filter: blur(6px)"
        segment_new_capture = true;
    })
    .catch(error => {
        console.log('Error setting up ASIC segment readout: ' + error);
    });
}

function update_loki_asic_segment_readout() {
    // Check if there is a segment image ready to be displayed
    carrier_endpoint.get('ASIC_SEGMENT_CAPTURE', timeout=ajax_timeout_ms)
    .then(response => {
        if (response.ASIC_SEGMENT_CAPTURE == 1) {
            // Reload only if the currently valid image is new
            if (segment_new_capture) {
                timestamp = new Date().getTime();   // Force update in this instance
                document.getElementById("segment-img").src="imgout/segment.png?t=" + timestamp;

                // Remove blurring
                document.getElementById("segment-img").style="-webkit-filter: blur(0px)"

                segment_new_capture = false;
                //console.log('segment display updated');
            } else {
                //console.log('segment not updated (old)');
            }
        } else if (response.ASIC_SEGMENT_CAPTURE != 1) {
            //document.getElementById("segment-img").src="";
            // Apply a blurring effect to demonstrate that the image is no longer valid
            document.getElementById("segment-img").style="-webkit-filter: blur(6px)"
            segment_new_capture = true;
            //console.log('There was no segment image to display, capture ready: ' + response.ASIC_SEGMENT_CAPTURE);
        }
    })
    .catch(error => {
        console.log('failed to get segment image: ' + error);
    });
}

var time_last_connected = null
function update_loki_connection() {
	// Exists simply to check if the Zynq is connected and report time since last connection
    // Uses VREG_EN because this will return quickly (simply getting the full tree takes some time)
    carrier_endpoint.get('VREG_EN', timeout=ajax_timeout_ms)
    .then(response => {
        time_last_connected = new Date()
		$('#zynq-connection-state').html("Connected");
		$('#zynq-connection-state').removeClass();
		$('#zynq-connection-state').addClass("badge bg-success");
    })
    .catch(error => {
	    timenow = new Date();
	    seconds_down = Math.round(((timenow.getTime() - time_last_connected.getTime())/1000))
        $('#zynq-connection-state').html("No Connection for " + seconds_down + "s");
        $('#zynq-connection-state').removeClass();
        $('#zynq-connection-state').addClass("badge bg-warning");
        console.log('failed to get connection: ' + error);
    });
}

function update_loki_asic_frame_length() {
    carrier_endpoint.get('ASIC_FRAME_LENGTH', timeout=ajax_timeout_ms)
    .then(response => {
        frame_length = response.ASIC_FRAME_LENGTH;

        // Update the badge
        $('#asic-frame-length-state').html((frame_length + " cycles"));
        $('#asic-frame-length-state').removeClass();
        $('#asic-frame-length-state').addClass("badge bg-success");
    })
    .catch(error => {
        $('#asic-frame-length-state').html(("No Con"));
        $('#asic-frame-length-state').removeClass();
        $('#asic-frame-length-state').addClass("badge bg-warning");
        console.log('failed to get frame length: ' + error);
    });
}

function update_loki_asic_sync() {
    carrier_endpoint.get('SYNC', timeout=ajax_timeout_ms)
    .then(response => {
        asic_sync_state = response.SYNC;

        //TODO set the zynq button state with asic_sync_sel

        // If the aux sync is selected, the value read is for the zynq
        // setting only, and not the asic one.
        if (!asic_sync_sel_aux) {
            $('#asic-sync-state').html((asic_sync_state ? "High" : "Low"));
            $('#asic-sync-state').removeClass();
            $('#asic-sync-state').addClass((asic_sync_state ? "badge bg-success" : "badge bg-danger"));
        } else {
            $('#asic-sync-state').html("AUX");
            $('#asic-sync-state').removeClass();
            $('#asic-sync-state').addClass("badge bg-warning");
        }

        //console.log("Got asic sync state: " + asic_sync_state)
    })
    .catch(error => {
        $('#asic-sync-state').html("No Con");
        $('#asic-sync-state').removeClass();
        $('#asic-sync-state').addClass("badge bg-warning");
        console.log('Error retrieving SYNC reset state: ' + error);
    });
}

var asic_sync_sel_aux = NaN;

function update_loki_asic_sync_aux(){
    carrier_endpoint.get('SYNC_SEL_AUX', timeout=ajax_timeout_ms)
    .then(response => {
        asic_sync_sel_aux = response.SYNC_SEL_AUX;

        // The asic sync state is also updated based on this selection;
        // if aux is selected, the synq sync setting is not relevant.

        //TODO update and enable the radio buttons           

        //console.log("Got asic sync sel aux state: " + asic_sync_sel_aux)
    })
    .catch(error => {
        console.log('Error retrieving SYNC SEL AUX state: ' + error);
    });
}

function update_loki_asic_serialiser_mode() {
    carrier_endpoint.get('ASIC_SER_MODE', timeout=ajax_timeout_ms)
    .then(response => {
        asic_serialiser_mode = response.ASIC_SER_MODE;
        //console.log('Got serialiser mode ' + asic_serialiser_mode);

        $('#asic-ser-mode-state').html(asic_serialiser_mode);
        $('#asic-ser-mode-state').removeClass();
        switch (asic_serialiser_mode) {
            case "init":
                $('#asic-ser-mode-state').addClass("badge bg-info");
                break;
            case "bonding":
                $('#asic-ser-mode-state').addClass("badge bg-info");
                break;
            case "data":
                $('#asic-ser-mode-state').addClass("badge bg-success");
                break;
            default:
                //console.log('Serialiser mode not recognised: ' + asic_serialiser_mode);
                $('#asic-ser-mode-state').html("Unknown");
                $('#asic-ser-mode-state').addClass("badge bg-warning");
                break
        }
    })
    .catch(error => {
        $('#asic-ser-mode-state').html("No Con");
        $('#asic-ser-mode-state').removeClass();
        $('#asic-ser-mode-state').addClass("badge bg-warning");
        console.log('Error retrieving serialiser mode state: ' + error);
    });
}

function update_loki_asic_serialiser_pattern() {

}

var toast_shown = false;
$('.toast').on('shown.bs.toast', function() {
	toast_shown = true
})

function update_loki_critical_temp() {
	// Check to see if the temperature is currently critical, which shuts down regulators.
    carrier_endpoint.get('CRITICAL_TEMP', timeout=ajax_timeout_ms)
    .then(response => {
        critical_temp_state = response.CRITICAL_TEMP;
        //TODO send popup, add UI elements etc

        if (critical_temp_state) {
            if(!toast_shown) $('.toast').toast('show');
            console.log('Critical temperature reported (latest ' + latest_asic_temp + ')');
            $('#latest_critical_temperature').html(latest_asic_temp);
	    } else {
            $('.toast').toast('hide');
		    toast_shown = false;
	    }

        //console.log("Got critical temperature state: " + critical_temp_state)
    })
    .catch(error => {
        console.log('Error retrieving critical temperature state: ' + error);
    });
}


function change_ff_ch_dis(disabled, ff, ch) {
    carrier_endpoint.put(disabled, '/FIREFLY' + ff + '/CHANNELS/CH' + ch + '/Disabled', timeout=ajax_timeout_ms)
    .then((response) => {
        update_loki_ff_data();
        console.log("Firefly " + ff + " CH " + ch + " Disable Changed to " + (disabled ? "true" : "false"));
    })
    .catch(error => {
        console.log("Error setting Firefly " + ff + " CH " + ch + " Disable: " + error);
    });
}

function change_vcal() {
	var newcal = Number($('#vcal-input').prop('value'));
    carrier_endpoint.put(newcal, 'VCAL', timeout=ajax_timeout_ms)
    .then((response) => {
        update_loki_vcal();
        console.log("VCAL Set to " + newcal);
    })
    .catch(error => {
        console.log('Error setting VCAL voltage: ' + error);
    });
}

function set_calibration_pattern_highlight(sector, division) {
    carrier_endpoint.put(division, 'ASIC_CAL_PATTERN/HIGHLIGHT_DIVISION', timeout=ajax_timeout_ms)
    .then((response) => carrier_endpoint.put(sector, 'ASIC_CAL_PATTERN/HIGHLIGHT_SECTOR', timeout=ajax_timeout_ms))
    .then((response) => carrier_endpoint.put('highlight', 'ASIC_CAL_PATTERN/PATTERN', timeout=ajax_timeout_ms))
    .catch(error => {
        console.log('Error setting calibration pattern highlight sector: ' + error);
    });
}

function set_calibration_pattern_default() {
    carrier_endpoint.put('default', 'ASIC_CAL_PATTERN/PATTERN', timeout=ajax_timeout_ms)
    .then((response) => {
            console.log('Set calibration pattern to default');
    })
    .catch(error => {
        console.log('Error setting calibration pattern to default: ' + error);
    });
}

function set_calibration_pattern_enable(pattern_en) {
    carrier_endpoint.put(pattern_en, 'ASIC_CAL_PATTERN/ENABLE', timeout=ajax_timeout_ms)
    .catch(error => {
        console.log('Error setting calibration pattern enable: ' + error);
    })
}

function callback_CalPatternEn_Switch(event, state) {
    if ($("[name='cali-pattern-en']").bootstrapSwitch('disabled')) {
        // Ignore if the switch is disabled
    } else {
        console.log("Calibration pattern enable switch fired with disable state " + !state);
        set_calibration_pattern_enable(state)
        $("[name='cali-pattern-en']").bootstrapSwitch('disabled', true);    // Disable until next read
    }
}

function update_loki_asic_cal_pattern_en() {
    carrier_endpoint.get('ASIC_CAL_PATTERN/ENABLE', timeout=ajax_timeout_ms)
    .then(response => {
            cal_pattern_en = response.ENABLE;

            //console.log('Got calibration pattern enable as ' + cal_pattern_en);
            //TODO somehow set the radio state
            $("[name='cali-pattern-en']").bootstrapSwitch();
            $("[name='cali-pattern-en']").bootstrapSwitch('onText', 'Enabled');
            $("[name='cali-pattern-en']").bootstrapSwitch('offText', 'Disabled');
            $("[name='cali-pattern-en']").bootstrapSwitch('offColor', 'danger');
            $("[name='cali-pattern-en']").bootstrapSwitch('disabled', false);
            //$("input[name='"+switchname+"']").on('switchChange.bootstrapSwitch', function(event,state) {
            $("[name='cali-pattern-en']").bootstrapSwitch('onSwitchChange', callback_CalPatternEn_Switch);
            if (cal_pattern_en) {
                $("[name='cali-pattern-en']").bootstrapSwitch('state', true);
            } else {
                $("[name='cali-pattern-en']").bootstrapSwitch('state', false);
            }
    })
    .catch(error => {
            console.log('Error retrieving calibration pattern enable state: ' + error);
    });
}

function change_sync_sel_aux(aux_en) {
    carrier_endpoint.put(aux_en, 'SYNC_SEL_AUX', timeout=ajax_timeout_ms)
    .catch(error => {
        console.log('Error setting sync input selection: ' + error);
    })
    .then(response => {
        //TODO disable the radio until it is read back
        $("sync_aux_radio").addClass('disabled');
        $('btnradio1').prop('disabled', true);
        // $("btnradio1").attr("disabled", true);
    });
}

function change_asic_mode(modename) {
	// Re-init the ASIC and set mode, local or global.
	// Currently, only global is supported
    carrier_endpoint.put(modename, 'ASIC_MODE', timeout=ajax_timeout_ms)
    .then(response => {
		console.log("Mode set to " + modename);
    })
    .catch(error => {
        console.log("Error setting ASIC mode: " + error);
    });
}

function change_feedback_cap(capacitance) {
    carrier_endpoint.put(capacitance, 'ASIC_FEEDBACK_CAPACITANCE', timeout=ajax_timeout_ms)
    .then(response => {
		console.log("Mode set to " + capacitance);
    })
    .catch(error => {
        console.log("Error setting feedback capacitance: " + error);
	});
}

function change_integration_time(frames) {
	frames = Number(frames)
    carrier_endpoint.put(frames, 'ASIC_INTEGRATION_TIME', timeout=ajax_timeout_ms)
    .then(response => {
		// Mark the readback void
		$('#asic-integration-time-state').removeClass();
		$('#asic-integration-time-state').addClass("badge bg-warning");

		console.log("Integration time set to " + frames + " frames");
    })
    .catch(error => {
        console.log("Error setting integration time: " + error);
	});
}

function change_frame_length(cycles) {
	cycles = Number(cycles)
    carrier_endpoint.put(cycles, 'ASIC_FRAME_LENGTH', timeout=ajax_timeout_ms)
    .then(response => {
		// Mark the readback void
		$('#asic-frame-length-state').removeClass();
		$('#asic-frame-length-state').addClass("badge bg-warning");

		console.log("Frame length set to " + cycles + " cycles");
    })
    .catch(error => {
        console.log("Error setting frame length: " + error);
	});
}

function change_serialiser_mode(modename) {
    carrier_endpoint.put(modename, 'ASIC_SER_MODE', timeout=ajax_timeout_ms)
    .then(response => {
		console.log("Serialiser mode set to " + modename);
    })
    .catch(error => {
        console.log("Error settting serialiser mode: " + error);
	});
}

function change_serialiser_all_pattern(pattern) {
    carrier_endpoint.put(pattern, 'ASIC_SER_PATTERN', timeout=ajax_timeout_ms)
    .then(response => {
		console.log("Serialiser pattern set to " + pattern);
    })
    .catch(error => {
        console.log("Error setting serialiser pattern: " + error);
	});
}

function run_vreg_powerdown() {
	console.log("Commanding adapter to power down VREG");
    carrier_endpoint.put(false, 'VREG_EN', timeout=ajax_timeout_ms)
    .then(response => {
        console.log("Powered down VREG_EN");
	})
    .catch(error => {
        console.log("Error powering down VREG_EN: " + error);
	});
}

function run_vreg_cycle() {
	console.log("Commanding adapter to power cycle VREG");
    carrier_endpoint.put(true, 'VREG_CYCLE', timeout=ajax_timeout_ms)
    .then(response => {
		$('#power-cycle-spinner').show()
	})
    .catch(error => {
        console.log("Error triggering VREG_EN power cycle: " + error);
	});

	// Re-run static data capture
    	//update_loki_ff_static_data();
}

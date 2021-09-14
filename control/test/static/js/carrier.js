api_version = '0.1';
// adapter_name = 'loki';
adapter_name = 'carrier';

$( document ).ready(function() {

    // Init UI
    init();

    update_api_version();
    update_api_adapters();

    // Loki additions
    update_loki_ff_static_data();
    poll_loki();
    poll_loki_slow();
});

function init() {

    // Generate the firefly channel switches
    document.getElementById('ff1_chtable').innerHTML = generateFireFlyChannelTable(1,
        12,     // 12 Channels
        3,      // Arrange in 3 columns
        false); // Do not include additional state column (indicated by switch)
    generateFireFlyChannelSwitches(1, 12);
    document.getElementById('ff2_chtable').innerHTML = generateFireFlyChannelTable(2,
        12,     // 12 Channels
        3,      // Arrange in 3 columns
        false); // Do not include additional state column (indicated by switch)
    generateFireFlyChannelSwitches(2, 12);

    init_power_tracking()
}

function update_api_version() {
    $.getJSON('/api', function(response) {
        $('#api-version').html(response.api);
        api_version = response.api;
    });
}

function update_api_adapters() {
    $.getJSON('/api/' + api_version + '/adapters/', function(response) {
        adapter_list = response.adapters.join(", ");
        $('#api-adapters').html(adapter_list);
    });
}

function poll_loki() {
	update_loki_ff_data();		// Updated in adapter at slower rate
	update_loki_power_monitor();	// Updated in adapter at slower rate
	update_loki_vcal();		// Held internal to adapter, no bus impact

	setTimeout(poll_loki, 1000);
}

function poll_loki_slow() {
	/* Items that change slowly, to avoid pointlessly quick refresh */
	update_loki_temps();		// Bus interaction every call

	setTimeout(poll_loki_slow, 4000);
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
            responsive: true,
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
            responsive: true,
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

    // Create the HTML
    var ret = `
                    <div class="row">
                        <p class="lead">FireFly ${id}</p>
                    </div>
                    <div class="row contflex">
                        <div clas="col-md-6">
                            <p>Manufacturer:&nbsp;
                                <span id="firefly-${id}-venid">&nbsp;</span>
                                , Product: 
                                <span id="firefly-${id}-prodid">&nbsp;</span>
                            </p>
                        </div>
                        <div clas="col-md-6">
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
                                    <th>Channel</th>
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


function update_loki_ff_static_data() {
    // FireFly General Information
    for (let ff_id = 1; ff_id <=2; ff_id++) {
        var firefly_vendorid = "";
        var firefly_product = "";

        // Vendor ID
        $.getJSON('/api/' + api_version + '/' + adapter_name + '/FIREFLY'+ff_id+'/VENDORID', function(response) {
            firefly_vendorid = response.VENDORID;
            //console.log("Got FireFly VendorID: "+firefly_vendorid);
            $('#firefly-'+ff_id+'-venid').html(firefly_vendorid);
            $('#firefly-'+ff_id+'-venid').removeClass();
            $('#firefly-'+ff_id+'-venid').addClass("label label-info");
        })
        .error(function(data) {
            // If there is no response to from the FireFly query, indicate this
            $('#firefly-'+ff_id+'-venid').html('NO RESPONSE');
            $('#firefly-'+ff_id+'-venid').removeClass();
            $('#firefly-'+ff_id+'-venid').addClass("label label-warning");
        });

        // Part Number
        $.getJSON('/api/' + api_version + '/' + adapter_name + '/FIREFLY'+ff_id+'/PARTNUMBER', function(response) {
            firefly_product = response.PARTNUMBER;
            console.log(document.getElementById('firefly-'+ff_id+'-prodid'));
            $('#firefly-'+ff_id+'-prodid').html(firefly_product);
            $('#firefly-'+ff_id+'-prodid').removeClass();
            $('#firefly-'+ff_id+'-prodid').addClass("label label-info");
        })
        .error(function(data) {
            // If there is no response to from the FireFly query, indicate this
            $('#firefly-'+ff_id+'-prodid').html('NO RESPONSE');
            $('#firefly-'+ff_id+'-prodid').removeClass();
            $('#firefly-'+ff_id+'-prodid').addClass("label label-warning");
        });
    }
}

function update_loki_ff_data() {
	// Channel States
    for (let ff_id = 1; ff_id <=2; ff_id++) {
        $.getJSON('/api/' + api_version + '/' + adapter_name + '/FIREFLY'+ff_id+'/CHANNELS', function(response) {

            // FireFly Disabled Channels
            var firefly_ch_dis = response.CHANNELS;
            var firefly_ch_dis_ch0 = response.CHANNELS.CH0.Disabled;
            var channel_states = "";

            for (const [key, value] of Object.entries(firefly_ch_dis)) {
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
        .error(function(data) {
            // If there is no response from the firefly query, disable the channel switches
            //console.log("No response to FireFly "+ff_id+" query");
            for (channel_num = 0; channel_num < 12; channel_num++) {
                $("[name='firefly-"+ff_id+"-CH"+channel_num+"-switch']").bootstrapSwitch('disabled', true);
            }

        });
    }
}

function update_loki_temps() {
	// FireFly Temperatures
    for (let ff_id = 1; ff_id <=2; ff_id++) {
        $.getJSON('/api/' + api_version + '/' + adapter_name + '/FIREFLY'+ff_id+'/TEMPERATURE/', function(response) {
            var firefly_temp = response.TEMPERATURE.toFixed(2);
            console.log("FireFly "+ff_id+" temperature: "+firefly_temp);
            $('#temp-firefly'+ff_id).html(firefly_temp);
        })
        .error(function(data) {
            $('#temp-firefly'+ff_id).html("N/A");
        });
    }

	// Other System Temperatures
	$.getJSON('/api/' + api_version + '/' + adapter_name + '/TEMPERATURES', function(response) {
		// Ambient Temperature
		var temp_ambient = response.TEMPERATURES.AMBIENT.toFixed(2)
		$('#temp-ambient').html(temp_ambient)

		// PT100 Temperature
		// TODO

		// ASIC TEMP1 Temperature
		// TODO

		// ASIC TEMP2 Temperature
		// TODO
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

	//$.getJSON('/api/' + api_version + '/' + adapter_name + '/PSU', function(response) {
	$.ajax({url:'/api/' + api_version + '/' + adapter_name + '/PSU',
		async: false,
		dataType: 'json',
		timeout: 200,
		success: function(response) {
			psu_analogue_pwr = response.PSU.ANALOGUE.POWER.toFixed(5);
			psu_dig_pwr = response.PSU.DIG.POWER.toFixed(5);
			psu_dig_ctrl_pwr = response.PSU.DIG_CTRL.POWER.toFixed(5);
			$('#psu-analogue-pwr').html(psu_analogue_pwr);
			$('#psu-dig-pwr').html(psu_dig_pwr);
			$('#psu-dig-ctrl-pwr').html(psu_dig_ctrl_pwr);

			psu_analogue_vol = response.PSU.ANALOGUE.VOLTAGE.toFixed(5);
			psu_dig_vol = response.PSU.DIG.VOLTAGE.toFixed(5);
			psu_dig_ctrl_vol = response.PSU.DIG_CTRL.VOLTAGE.toFixed(5);
			$('#psu-analogue-vol').html(psu_analogue_vol);
			$('#psu-dig-vol').html(psu_dig_vol);
			$('#psu-dig-ctrl-vol').html(psu_dig_ctrl_vol);

			psu_analogue_cur = response.PSU.ANALOGUE.CURRENT.toFixed(5);
			psu_dig_cur = response.PSU.DIG.CURRENT.toFixed(5);
			psu_dig_ctrl_cur = response.PSU.DIG_CTRL.CURRENT.toFixed(5);
			$('#psu-analogue-cur').html(psu_analogue_cur);
			$('#psu-dig-cur').html(psu_dig_cur);
			$('#psu-dig-ctrl-cur').html(psu_dig_ctrl_cur);
		},
		error: function() {
			console.log('Error retrieving power supply data');
		}
	}).fail(function(xhr, status) {
		console.log('fail');
	});

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
        /*power_tracking_time.push(
            dt.getHours().toString() + ':' +
            dt.getMinutes().toString() + ':' +
            dt.getSeconds().toString()
        );*/
        power_tracking_time.push(
	    dt.toISOString()
        );
        if (power_tracking_time.length > power_tracking_valuelimit) power_tracking_time.shift();

        chart_vol.update();
        chart_cur.update();

}

function update_loki_vcal() {
	$.getJSON('/api/' + api_version + '/' + adapter_name + '/VCAL', function(response) {
		var vcal = response.VCAL;
		$('#vcal-voltage').html(vcal);
	});
}

function change_ff_ch_dis(disabled, ff, ch) {
	console.log("Firefly " + ff + " CH " + ch + " Disable Changed to " + (disabled ? "true" : "false"));
	$.ajax({
		type: "PUT",
		url: '/api/' + api_version + '/' + adapter_name + '/FIREFLY' + ff + '/CHANNELS/CH' + ch,
		contentType: "application/json",
		data: JSON.stringify({'Disabled': disabled}),
        success: function(data) {
            // Update the channel disable list on success
            update_loki_ff_data();
        }
	});
}

function change_vcal() {
	var newcal = Number($('#vcal-input').prop('value'));
	console.log("VCAL Set to " + newcal);
	$.ajax({
		type: "PUT",
		url: '/api/' + api_version + '/' + adapter_name,
		contentType: "application/json",
		data: JSON.stringify({'VCAL': newcal}),
        success: function(data) {
            // Update the displayed vcal reading on success
            update_loki_vcal();
        }
	});
}

function run_vreg_cycle() {
	console.log("Commanding adapter to power cycle VREG");
	$.ajax({
		type: "PUT",
		url: '/api/' + api_version + '/' + adapter_name,
		contentType: 'application/json',
		data: JSON.stringify({'VREG_CYCLE': true}),
	success: function(data) {
	}
	});

	// Re-run static data capture
    	update_loki_ff_static_data();
}
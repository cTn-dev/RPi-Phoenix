$(document).ready(function() {     
    alive_refference = setInterval("alive()", 4000);
    battery_refference = setInterval("battery_status()", 10000);
    
    div_throttle = $('div#throttle');
    div_rudder = $('div#rudder');
    
    div_elevator = $('div#elevator');
    div_aileron = $('div#aileron');
    
    // request current state and current battery status
    values_state();
    battery_status();
    
    $(document).keydown(function(event) {
        if(keys_down[event.which] == undefined) {
            // create new object
            
            keys_down[event.which] = {};
        }    

        if(keys_down[event.which]['timer'] == undefined) {
            keypress(event.which);
        } 
    });
    
    $(document).keyup(function (event) {
        if(keys_down[event.which] != undefined) {
            // clear timeout and remove object
            
            clearTimeout(keys_down[event.which]['timer']);
            delete keys_down[event.which];
        }    
    });
    
});

var div_throttle, 
    div_rudder,
    div_elevator,
    div_aileron,
    keys_down = {},
    state;    

    
function values_state() {
    $.ajax('/state', {
        dataType: "json",
        success: function(data) {
            $('div#status div.wrapper').append('<p>Current State ... <span class="green">Loaded</span></p>');
            $('div#status').scrollTop($('div#status div.wrapper').height());
            state = data;
            
            throttle_marker(state.throttle);
            rudder_marker(state.rudder);
            elevator_marker(state.elevator);
            aileron_marker(state.aileron);
        }
    });    
} 

 
var alive_error = 0;
function alive() {
    $.ajax('/alive', {
        success: function() {
            if (alive_error) {
                $('div#status div.wrapper').append('<p>Connection <span class="green">re-established</span></p>');
                $('div#status').scrollTop($('div#status div.wrapper').height());   
                
                values_state();
                alive_error = 0;
            }
        },
        error: function() {
            $('div#status div.wrapper').append('<p>Connection <span class="red">Lost</span> ... trying to reconnect</p>');
            $('div#status').scrollTop($('div#status div.wrapper').height());
            alive_error = 1;
        }
    });  
} 

function battery_status() {
    $.ajax('/battery', {
        success: function(data) {
            $('div#info span.battery').html(data);
        }
    });    
} 
    
function throttle_marker(num) {
    var e = div_throttle;
    var height = e.height() - 10;
    var pos = height - ((height / 100) * num);
    
    $('div.marker', e).css('margin-top', pos + 'px');
    $('div#throttle-status').html(num + '%');
}

function rudder_marker(num) {
    var e = div_rudder;
    var width = (e.width() - 10) / 2;
    var pos = width + ((width / 100) * num);    
    
    $('div.marker', e).css('margin-left', pos + 'px');
    $('div#rudder-status').html(num + '%');
}

function elevator_marker(num) {
    var e = div_elevator;
    var height = (e.height() - 10) / 2;
    var pos = height + (height / 100) * num;
    
    $('div.marker', e).css('margin-top', pos + 'px');
    $('div#elevator-status').html(num + '%');
}

function aileron_marker(num) {
    var e = div_aileron;
    var width = (e.width() - 10) / 2;
    var pos = width + ((width / 100) * num);
    
    $('div.marker', e).css('margin-left', pos + 'px');
    $('div#aileron-status').html(num + '%');
}

function keypress(key) {;
    switch(key) {
        case 37:
            arrow_left();
        break;
        case 38:
            arrow_up();
        break;
        case 39:
            arrow_right();
        break;
        case 40:
            arrow_down();
        break;
        case 65:
            key_a();
        break;
        case 68:
            key_d();
        break;
        case 83:
            key_s();
        break;
        case 87:
            key_w();
        break;            
    }
}

function arrow_left() {
    var which = 37;
    
    if (state.rudder > -100) {
        $.ajax('/command/rudder/' + (state.rudder - 1), {
            success: function(data) {
                if (data == 'true') {
                    if (state.rudder > -100) { // protection against delayed commands
                        state.rudder--; // saves current state
                        rudder_marker(state.rudder); // updates gui with current values
                    }  
                }                 
            }
        });   
    }  

    if(keys_down[which]['timer'] == undefined) {
        keys_down[which]['timer'] = setTimeout("arrow_left()", 250);
    } else {
        keys_down[which]['timer'] = setTimeout("arrow_left()", 50);
    } 
}

function arrow_up() {
    var which = 38;
    
    if (state.throttle < 100) {
        $.ajax('/command/throttle/' + (state.throttle + 1), {
            success: function(data) {
                if (data == 'true') {
                    if (state.throttle < 100) {
                        state.throttle++;
                        throttle_marker(state.throttle);
                    }
                }
            }
        });
    }
    
    if(keys_down[which]['timer'] == undefined) {
        keys_down[which]['timer'] = setTimeout("arrow_up()", 250);
    } else {
        keys_down[which]['timer'] = setTimeout("arrow_up()", 50);
    }     
}

function arrow_right() {
    var which = 39;
    
    if (state.rudder < 100) {
        $.ajax('/command/rudder/' + (state.rudder + 1), {
            success: function(data) {
                if (data == 'true') {
                    if (state.rudder < 100) {
                        state.rudder++;
                        rudder_marker(state.rudder);
                    }
                }
            }
        });   
    }  
 
    if(keys_down[which]['timer'] == undefined) {
        keys_down[which]['timer'] = setTimeout("arrow_right()", 250);
    } else {
        keys_down[which]['timer'] = setTimeout("arrow_right()", 50);
    }   
}

function arrow_down() {
    var which = 40;
    
    if (state.throttle > 0) {
        $.ajax('/command/throttle/' + (state.throttle - 1), {
            success: function(data) {
                if (data == 'true') {
                    if (state.throttle > 0) {
                        state.throttle--;
                        throttle_marker(state.throttle);
                    }
                }
            }
        });   
    }
    
    if(keys_down[which]['timer'] == undefined) {
        keys_down[which]['timer'] = setTimeout("arrow_down()", 250);
    } else {
        keys_down[which]['timer'] = setTimeout("arrow_down()", 50);
    }      
}


function key_a() {
    var which = 65;
    
    if (state.aileron > -100) {
        $.ajax('/command/aileron/' + (state.aileron - 1), {
            success: function(data) {
                if (data == 'true') {
                    if (state.aileron > -100) {
                        state.aileron--;
                        aileron_marker(state.aileron);
                    }
                }
            }
        });
    }
    
    if(keys_down[which]['timer'] == undefined) {
        keys_down[which]['timer'] = setTimeout("key_a()", 250);
    } else {
        keys_down[which]['timer'] = setTimeout("key_a()", 50);
    }       
}

function key_d() {
    var which = 68;

    if (state.aileron < 100) {
        $.ajax('/command/aileron/' + (state.aileron + 1), {
            success: function(data) {
                if (data == 'true') {
                    if (state.aileron < 100) {
                        state.aileron++;
                        aileron_marker(state.aileron);
                    }
                }
            }
        });
    }
    
    if(keys_down[which]['timer'] == undefined) {
        keys_down[which]['timer'] = setTimeout("key_d()", 250);
    } else {
        keys_down[which]['timer'] = setTimeout("key_d()", 50);
    }     
}

function key_s() {
    var which = 83;
    
    if (state.elevator > -100) {
        $.ajax('/command/elevator/' + (state.elevator - 1), {
            success: function(data) {
                if (data == 'true') {
                    if (state.elevator > -100) {
                        state.elevator--;
                        elevator_marker(state.elevator);
                    }
                }
            }
        });
    }
    
    if(keys_down[which]['timer'] == undefined) {
        keys_down[which]['timer'] = setTimeout("key_s()", 250);
    } else {
        keys_down[which]['timer'] = setTimeout("key_s()", 50);
    }     
}

function key_w() {
    var which = 87;

    if (state.elevator < 100) {
        $.ajax('/command/elevator/' + (state.elevator + 1), {
            success: function(data) {
                if (data == 'true') {
                    if (state.elevator < 100) {
                        state.elevator++;
                        elevator_marker(state.elevator);
                    }
                }
            }
        });
    }
    
    if(keys_down[which]['timer'] == undefined) {
        keys_down[which]['timer'] = setTimeout("key_w()", 250);
    } else {
        keys_down[which]['timer'] = setTimeout("key_w()", 50);
    }     
}

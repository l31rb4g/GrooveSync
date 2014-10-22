window.$_BBQ = {

    sw: 1,

    response: true,

    request: function(action, params, callback){
        if (!params) params = [];
        this.callback = callback;
        window.location = '#BBQ' + this.sw + '::' + action + '|' + JSON.stringify(params);
        this.sw = (this.sw == 1 ? 2 : 1);
    },

    execute_callback: function(content){
        content = decodeURIComponent(content);
        this.callback(content);
    },

    getResponse: function(){
        return decodeURIComponent(this.response);
    }

};

window.Barbacoa = {

    version: 0.1,

    plugins: {},

    Plugin: function(map){
        map.plugin = $_BBQ.plugin_being_registred;
        map.execute = function(className, method, args){
            $_BBQ.request('execute-plugin', [map.plugin, className, method, args]);
            return $_BBQ.response;
        };
        Barbacoa.plugins[$_BBQ.plugin_being_registred] = map;
    },

    File: {
        write: function(filename, content) {
            $_BBQ.request('File.write', [filename, content]);
            return $_BBQ.response;
        },
        choose_directory: function(selected_dir) {
            $_BBQ.request('File.choose_directory', [selected_dir]);
            return $_BBQ.response;
        }
    },

    Environment: {
        get_user_home: function(){
            $_BBQ.request('Environment.get_user_home', []);
            return $_BBQ.getResponse();
        }

    }

};

$_BBQ.request('load-plugins');
if (typeof(BarbacoaReady) == 'function'){
    BarbacoaReady();
}
new Barbacoa.Plugin({

    getUserData: function(username){
        return this.execute('GrooveSync', 'getUserData', [username]);
    }

});
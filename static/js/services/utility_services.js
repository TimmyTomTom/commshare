(function() {
  'use strict';

  var module = angular.module('communityshare.services.utility', []);

  module.filter('truncate', function () {
    return function (text, length, end) {
      if (end === undefined)
        end = "...";
      var output;
      if ((text.length <= length) || (text.length - end.length <= length)) {
        output = text;
      }
      else {
        output = String(text).substring(0, length-end.length) + end;
      }
      return output 
    };
  });

  module.factory('parseyyyyMMdd', function() {
    return function(yyyyMMdd) {
      var date = new Date(yyyyMMdd.substring(0, 4), yyyyMMdd.substring(4, 6),
                          yyyyMMdd.substring(6, 8));
      date.setMonth(date.getMonth()-1);
      return date;
    };
  });


})();

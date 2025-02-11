this.ckan.module("news-actions", function ($) {
    "use strict";
  
    return {
      options: {
        subjectId: null,
        subjectType: null,
        ajaxReload: null,
      },
      initialize: function () {
        console.log("news-actions module initialized");  // Debugging
        $.proxyAll(this, /_on/);
        this.$(".news-actions .news-visibility-toggler").on(
          "click",
          this._onToggleNews
        );
      },
      teardown: function () {
        this.$(".news-action.news-visibility-toggler").off(
          "click",
          this._onToggleNews
        );
      },
      _onToggleNews: function (e) {
        console.log("Toggle button clicked"); // Debugging
        var id = e.currentTarget.dataset.id;
        var ajaxReload = this.options.ajaxReload;
  
        this.sandbox.client.call(
          "POST",
          "ckanext_news_toggle_visibility",
          { id: id },
          function (e) {
            console.log("Visibility toggled"); // Debugging
            if (ajaxReload) {
              $(".modal").modal("hide");
              $(document).trigger("news:changed");
            } else {
              window.location.reload();
            }
          }
        );
      },
    };
});
